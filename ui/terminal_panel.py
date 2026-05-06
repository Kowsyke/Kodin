# Kodin - ui/terminal_panel.py
#
# TerminalPanel: embedded pty shell. Uses threading.Thread directly.
# Spawns $SHELL (fallback /bin/bash) in the directory of the open file.

from __future__ import annotations

import os
import re
import select
import signal
import threading
from pathlib import Path

from textual.widget import Widget
from textual.widgets import Static, RichLog
from textual.app import ComposeResult
from textual import events
from rich.text import Text
from rich.style import Style

_SHELL = os.environ.get("SHELL") or ("/bin/bash" if os.path.exists("/bin/bash") else "/bin/sh")
# FIX 3: also strip OSC sequences (title-setting escape codes used by some shells)
_ANSI_RE = re.compile(r"\x1b(?:\][^\x07]*\x07|\[[0-9;]*[A-Za-z]|[()][AB012]|\x1b)")

# FIX 5: keys that should pass through to the App rather than be consumed
_TERM_PASSTHROUGH = frozenset({"ctrl+b", "ctrl+t", "ctrl+k", "ctrl+q"})


class TerminalPanel(Widget):

    can_focus = True

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._master_fd: int | None = None
        self._pid: int | None = None
        self._cwd: str = str(Path.cwd())
        self._reader: threading.Thread | None = None

    def compose(self) -> ComposeResult:
        yield Static(f" TERMINAL  ({_SHELL})", classes="terminal-header")
        yield RichLog(id="term-log", wrap=False, highlight=False, markup=False)

    # FIX 1: shell starts lazily on first display, not on mount
    def on_mount(self) -> None:
        pass  # shell starts lazily on first display

    def watch_display(self, display: bool) -> None:
        if display and self._pid is None:
            self._start_shell()
            self.query_one("#term-log", RichLog).focus()

    def on_unmount(self) -> None:
        self._kill_shell()

    def set_cwd(self, filepath: str) -> None:
        """Update working directory. Takes effect on next shell start."""
        self._cwd = str(Path(filepath).parent)

    # ------------------------------------------------------------------
    # Shell lifecycle
    # ------------------------------------------------------------------

    def _start_shell(self) -> None:
        try:
            import pty
            pid, master_fd = pty.fork()
        except (OSError, ImportError) as exc:
            self._show_error(f"Cannot start terminal: {exc}")
            return

        if pid == 0:
            # Child process: exec shell
            try:
                os.chdir(self._cwd)
            except OSError:
                pass
            os.execv(_SHELL, [_SHELL])
            os._exit(1)

        self._pid = pid
        self._master_fd = master_fd

        # Set non-blocking so reads don't hang
        import fcntl
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

    def _kill_shell(self) -> None:
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

    def _read_loop(self) -> None:
        """Background thread: read pty output and push to RichLog."""
        try:
            log = self.query_one("#term-log", RichLog)
        except Exception:
            return

        # FIX 2: also check _pid in the while condition
        while self._master_fd is not None and self._pid is not None:
            try:
                r, _, _ = select.select([self._master_fd], [], [], 0.05)
                if not r:
                    continue
                data = os.read(self._master_fd, 4096)
                if not data:
                    break
                text = data.decode("utf-8", errors="replace")
                clean = _ANSI_RE.sub("", text).replace("\r", "")
                # FIX 4: removed `if stripped:` guard so blank lines are written
                for line in clean.splitlines(keepends=True):
                    stripped = line.rstrip("\n")
                    self.app.call_from_thread(
                        log.write,
                        Text(stripped, style=Style(color="#39d353")),
                    )
            except OSError:
                break

    # ------------------------------------------------------------------
    # Keyboard forwarding
    # ------------------------------------------------------------------

    # FIX 5: pass App-level keys through instead of stopping them
    async def on_key(self, event: events.Key) -> None:
        if event.key in _TERM_PASSTHROUGH:
            return  # let App handle these
        event.stop()
        if self._master_fd is None:
            return

        _map: dict[str, bytes] = {
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

        raw = _map.get(event.key)
        if raw:
            self._write(raw)
        elif event.character and len(event.character) == 1:
            self._write(event.character.encode("utf-8"))

    def _write(self, data: bytes) -> None:
        if self._master_fd is not None:
            try:
                os.write(self._master_fd, data)
            except OSError:
                pass

    def _show_error(self, msg: str) -> None:
        try:
            self.query_one("#term-log", RichLog).write(
                Text(msg, style=Style(color="#ff4444"))
            )
        except Exception:
            pass
