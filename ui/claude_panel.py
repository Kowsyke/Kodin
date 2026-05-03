# Kodin - ui/claude_panel.py
#
# ClaudePanel: toggleable sidebar widget for AI-assisted editing.
# Streams responses from claude-sonnet-4-6 via the Anthropic SDK.
# Conversation history is capped at 20 messages. Requires ANTHROPIC_API_KEY.

from __future__ import annotations

import os
import threading

from textual.widget import Widget
from textual.widgets import Static, RichLog, Input, Button
from textual.app import ComposeResult
from textual.message import Message
from textual._work_decorator import work
from rich.text import Text
from rich.style import Style


class ClaudePanel(Widget):

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._history: list[dict] = []
        self._context: str = ""
        self._api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")

    def compose(self) -> ComposeResult:
        yield Static(" CLAUDE", classes="claude-header")
        yield RichLog(id="claude-log", wrap=True, highlight=False, markup=False)
        yield Input(placeholder="Ask Claude...", id="claude-input")
        yield Button("Clear", id="claude-clear", variant="default")

    def on_mount(self) -> None:
        log = self.query_one("#claude-log", RichLog)
        if not self._api_key:
            log.write(Text(
                "ANTHROPIC_API_KEY not set.\nExport it and restart Kodin.",
                style=Style(color="#ff4444"),
            ))
        else:
            log.write(Text(
                "Claude ready. Ask anything about your code.",
                style=Style(color="#586069"),
            ))

    def set_context(self, line: str) -> None:
        """Called by the app when the panel opens; sets the current line as context."""
        self._context = line

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "claude-input":
            return
        prompt = event.value.strip()
        if not prompt:
            return
        event.input.clear()
        self._send_message(prompt)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "claude-clear":
            self._history.clear()
            self.query_one("#claude-log", RichLog).clear()

    def _send_message(self, prompt: str) -> None:
        if not self._api_key:
            return

        log = self.query_one("#claude-log", RichLog)
        log.write(Text(f"> {prompt}", style=Style(color="#00d4ff", bold=True)))

        system = "You are a coding assistant embedded in Kodin, a terminal code editor."
        if self._context:
            system += f"\n\nCurrent line context:\n{self._context}"

        self._history.append({"role": "user", "content": prompt})

        # Cap history at 20 messages (10 exchanges)
        if len(self._history) > 20:
            self._history = self._history[-20:]

        self._stream_response(system, list(self._history), log)

    @work(thread=True)
    def _stream_response(
        self,
        system: str,
        messages: list[dict],
        log: RichLog,
    ) -> None:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self._api_key)

            collected = []
            with client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=system,
                messages=messages,
            ) as stream:
                for chunk in stream.text_stream:
                    collected.append(chunk)
                    self.app.call_from_thread(
                        log.write,
                        Text(chunk, style=Style(color="#c9d1d9")),
                    )

            full_reply = "".join(collected)
            self._history.append({"role": "assistant", "content": full_reply})
            self.app.call_from_thread(
                log.write,
                Text(""),
            )

        except Exception as exc:
            self.app.call_from_thread(
                log.write,
                Text(f"Error: {exc}", style=Style(color="#ff4444")),
            )
