# Kodin - ui/terminal_panel.py
#
# TerminalPanel: toggleable embedded terminal using a pty subprocess.
# Spawns /bin/bash (fallback: /bin/sh) in the directory of the open file.
# Output is streamed into a RichLog. Input is forwarded via os.write to the pty.

from __future__ import annotations

import asyncio
import os
import pty
import fcntl
import termios
import struct
import signal
from pathlib import Path

from textual.widget import Widget
from textual.widgets import Static, RichLog
from textual.app import ComposeResult
from textual import events
from textual._work_decorator import work
from rich.text import Text
from rich.style import Style


_SHELL = "/bin/bash" if os.path.exists("/bin/bash") else "/bin/sh"


class TerminalPanel(Widget):

    can_focus = True

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._master_fd: int | None = None
        self._pid: int | None = None
        self._cwd: str = str(Path.cwd())
        self._reader_task: asyncio.Task | None = None

    def compose(self) -> ComposeResult:
        yield Static(" TERMINAL", classes="terminal-header")
        yield RichLog(id="term-log", wrap=False, highlight=False, markup=False)

    def on_mount(self) -> None:
        self._start_shell()

    def on_unmount(self) -> None:
        self._kill_shell()

    def set_cwd(self, path: str) -> None:
        """Called by the app when a new file is opened to set the working directory."""
        self._cwd = str(Path(path).parent)

    # --- shell lifecycle ---

    def _start_shell(self) -> None:
        try:
            pid, master_fd = pty.fork()
        except OSError:
            self._show_error("pty.fork() failed")
            return

        if pid == 0:
            # child: exec shell
            os.chdir(self._cwd)
            os.execv(_SHELL, [_SHELL])
            os._exit(1)

        self._pid = pid
        self._master_fd = master_fd

        # Set non-blocking
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        self._read_output()

    def _kill_shell(self) -> None:
        if self._reader_task is not None:
            self._reader_task.cancel()
            self._reader_task = None
        if self._pid is not None:
            try:
                os.kill(self._pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            self._pid = None
        if self._master_fd is not None:
            try:
                os.close(self._master_fd)
            except OSError:
                pass
            self._master_fd = None

    @work(thread=True)
    def _read_output(self) -> None:
        import select as sel
        log_ref = None
        try:
            log_ref = self.query_one("#term-log", RichLog)
        except Exception:
            return

        while self._master_fd is not None:
            try:
                r, _, _ = sel.select([self._master_fd], [], [], 0.1)
                if not r:
                    continue
                data = os.read(self._master_fd, 4096)
                if not data:
                    break
                text = data.decode("utf-8", errors="replace")
                # Strip basic ANSI escape sequences for clean display
                import re
                clean = re.sub(r"\x1b\[[0-9;]*[A-Za-z]|\x1b[()][AB012]|\r", "", text)
                for line in clean.splitlines(keepends=True):
                    self.app.call_from_thread(
                        log_ref.write,
                        Text(line.rstrip("\n"), style=Style(color="#39d353")),
                    )
            except OSError:
                break

    # --- keyboard forwarding ---

    async def on_key(self, event: events.Key) -> None:
        event.stop()

        if self._master_fd is None:
            return

        key = event.key
        char = event.character

        # Map special keys to control bytes
        mapping: dict[str, bytes] = {
            "enter": b"\r",
            "backspace": b"\x7f",
            "tab": b"\t",
            "escape": b"\x1b",
            "up": b"\x1b[A",
            "down": b"\x1b[B",
            "right": b"\x1b[C",
            "left": b"\x1b[D",
            "ctrl+c": b"\x03",
            "ctrl+d": b"\x04",
            "ctrl+l": b"\x0c",
            "ctrl+z": b"\x1a",
        }

        if key in mapping:
            self._write_to_pty(mapping[key])
        elif char is not None and len(char) == 1:
            self._write_to_pty(char.encode("utf-8"))

    def _write_to_pty(self, data: bytes) -> None:
        if self._master_fd is not None:
            try:
                os.write(self._master_fd, data)
            except OSError:
                pass

    def _show_error(self, msg: str) -> None:
        try:
            log = self.query_one("#term-log", RichLog)
            log.write(Text(f"Terminal error: {msg}", style=Style(color="#ff4444")))
        except Exception:
            pass
