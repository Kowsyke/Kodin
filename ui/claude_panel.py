# Kodin - ui/claude_panel.py
#
# ClaudePanel: AI assistant sidebar. Streams responses from claude-sonnet-4-6.
# Uses threading.Thread directly to avoid Textual version dependency on @work.
# Requires ANTHROPIC_API_KEY in the environment.

from __future__ import annotations

import os
import threading

from textual import events
from textual.widget import Widget
from textual.widgets import Static, RichLog, Input, Button
from textual.app import ComposeResult
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
        yield Button("Clear", id="claude-clear")

    def on_mount(self) -> None:
        log = self.query_one("#claude-log", RichLog)
        if not self._api_key:
            log.write(Text(
                "ANTHROPIC_API_KEY not set.\nSet it and restart Kodin.",
                style=Style(color="#ff4444"),
            ))
        else:
            log.write(Text(
                "Claude ready. Ask anything about your code.",
                style=Style(color="#586069"),
            ))

    def set_context(self, line: str) -> None:
        """Called by app when panel opens. Sets current line as context."""
        self._context = line

    async def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            event.stop()
            self.app.query_one("#editor").focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "claude-input":
            return
        prompt = event.value.strip()
        if not prompt or not self._api_key:
            return
        event.input.clear()
        self._send(prompt)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "claude-clear":
            self._history.clear()
            self.query_one("#claude-log", RichLog).clear()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _send(self, prompt: str) -> None:
        log = self.query_one("#claude-log", RichLog)
        log.write(Text(f"> {prompt}", style=Style(color="#00d4ff", bold=True)))

        system = (
            "You are a coding assistant embedded in Kodin, a terminal code editor. "
            "Give concise, practical answers. When showing code, use plain text "
            "without markdown fences since this is a terminal UI."
        )
        if self._context:
            system += f"\n\nCurrent line context:\n{self._context}"

        self._history.append({"role": "user", "content": prompt})
        if len(self._history) > 20:
            self._history = self._history[-20:]

        t = threading.Thread(
            target=self._stream,
            args=(system, list(self._history), log),
            daemon=True,
        )
        t.start()

    def _stream(self, system: str, messages: list[dict], log: RichLog) -> None:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self._api_key)
            collected: list[str] = []

            buf: list[str] = []
            with client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=system,
                messages=messages,
            ) as stream:
                for chunk in stream.text_stream:
                    collected.append(chunk)
                    buf.append(chunk)
                    combined = "".join(buf)
                    if "\n" in combined:
                        parts = combined.split("\n")
                        for part in parts[:-1]:
                            self.app.call_from_thread(
                                log.write,
                                Text(part, style=Style(color="#c9d1d9")),
                            )
                        buf = [parts[-1]]
            # Flush remaining
            remaining = "".join(buf)
            if remaining:
                self.app.call_from_thread(
                    log.write,
                    Text(remaining, style=Style(color="#c9d1d9")),
                )

            full_reply = "".join(collected)
            self._history.append({"role": "assistant", "content": full_reply})
            self.app.call_from_thread(
                log.write,
                Text("---", style=Style(color="#1e2a38")),
            )

        except Exception as exc:
            self.app.call_from_thread(
                log.write,
                Text(f"Error: {exc}", style=Style(color="#ff4444")),
            )
