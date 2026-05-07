# Kodin - ui/editor_widget.py
#
# EditorWidget: modal vim-style editing surface backed by TextBuffer.
# Uses render_line(y) -> Strip for per-line rendering, bypassing Textual's
# _layout_cache so the editor is always live. Posts StatusChanged on every
# state change so StatusBar stays in sync.

from __future__ import annotations

from textual.widget import Widget
from textual.strip import Strip
from textual import events
from textual.message import Message
from rich.segment import Segment
from rich.style import Style

from core.buffer import TextBuffer
from utils.files import load_file, save_file

NORMAL = "NORMAL"
INSERT = "INSERT"
COMMAND = "COMMAND"

# Keys the App handles globally -- EditorWidget lets them pass through.
_APP_KEYS = frozenset({"ctrl+b", "ctrl+t", "ctrl+k", "ctrl+q", "ctrl+s"})

# Precomputed styles (avoids constructing Style objects on every render_line call)
_S_TEXT    = Style(color="#c9d1d9")
_S_DIM     = Style(color="#586069")
_S_ACCENT  = Style(color="#00d4ff")
_S_TILDE   = Style(color="#586069", dim=True)
_S_LINE_BG = Style(bgcolor="#111827", color="#c9d1d9")
_S_CURSOR  = Style(bgcolor="#00d4ff", color="#0a0e14", bold=True)
_S_BG      = Style(bgcolor="#0a0e14")


class EditorWidget(Widget):
    """Modal vim-style editor surface backed by TextBuffer."""

    can_focus = True

    # ------------------------------------------------------------------
    # Message emitted on every state change so StatusBar can update.
    # ------------------------------------------------------------------
    class StatusChanged(Message):
        def __init__(
            self,
            mode: str,
            filepath: str,
            cursor_y: int,
            cursor_x: int,
            modified: bool,
            command_buf: str = "",
            status_msg: str = "",
        ) -> None:
            super().__init__()
            self.mode = mode
            self.filepath = filepath
            self.cursor_y = cursor_y
            self.cursor_x = cursor_x
            self.modified = modified
            self.command_buf = command_buf
            self.status_msg = status_msg

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.buffer = TextBuffer()
        self.filepath: str = ""
        self.mode: str = NORMAL
        self.command_buf: str = ""
        self._scroll_y: int = 0
        self._pending_d: bool = False
        self._pending_g: bool = False
        self._status_msg: str = ""

    def on_mount(self) -> None:
        self._post_status()
        self.refresh()

    # ------------------------------------------------------------------
    # Public API called by KodinApp
    # ------------------------------------------------------------------

    def load_file(self, path: str) -> None:
        self.filepath = path
        self.buffer.load(load_file(path))
        self._scroll_y = 0
        self.mode = NORMAL
        self.command_buf = ""
        self._status_msg = ""
        self._post_status()
        self.refresh()

    def save(self) -> None:
        if not self.filepath:
            self._status_msg = "No filename -- use :w <name>"
            return
        content = self.buffer.save()
        save_file(self.filepath, content)
        self._status_msg = f"Saved {self.filepath}"

    def get_selected_text(self) -> str:
        """Return the current line for Claude context."""
        return self.buffer.lines[self.buffer.cursor_y]

    # ------------------------------------------------------------------
    # Rendering -- one Strip per line, no global caching
    # ------------------------------------------------------------------

    def render_line(self, y: int) -> Strip:
        width = self.size.width
        if width <= 0:
            return Strip.blank(0)

        # Adjust scroll on the first line of each frame.
        if y == 0:
            self._adjust_scroll(self.size.height)

        lines = self.buffer.get_lines()
        num_lines = len(lines)
        gutter_w = max(len(str(num_lines)), 3) + 1

        line_idx = self._scroll_y + y
        cy = self.buffer.cursor_y
        cx = self.buffer.cursor_x
        is_cursor = (line_idx == cy)

        segs: list[Segment] = []
        used = 0

        if line_idx < num_lines:
            # Gutter
            num_str = f"{line_idx + 1:>{gutter_w - 1}} "
            segs.append(Segment(num_str, _S_ACCENT if is_cursor else _S_DIM))
            used += len(num_str)

            text_w = max(width - gutter_w, 0)
            line = lines[line_idx]

            if is_cursor:
                before = line[:cx][:text_w]
                segs.append(Segment(before, _S_LINE_BG))
                used += len(before)
                remaining = text_w - len(before)

                if remaining > 0:
                    cur_ch = line[cx] if cx < len(line) else " "
                    segs.append(Segment(cur_ch, _S_CURSOR))
                    used += 1
                    remaining -= 1

                if remaining > 0:
                    after = (line[cx + 1:] if cx < len(line) else "")[:remaining]
                    segs.append(Segment(after, _S_LINE_BG))
                    used += len(after)
                    remaining -= len(after)

                if remaining > 0:
                    segs.append(Segment(" " * remaining, _S_LINE_BG))
                    used += remaining
            else:
                text = line[:text_w]
                segs.append(Segment(text, _S_TEXT))
                used += len(text)
        else:
            # Past end of file -- tilde rows like vim
            gutter = " " * (gutter_w - 1) + " "
            segs.append(Segment(gutter, _S_DIM))
            used += len(gutter)
            segs.append(Segment("~", _S_TILDE))
            used += 1

        # Pad to widget width with plain background
        if used < width:
            segs.append(Segment(" " * (width - used), _S_BG))

        return Strip(segs, width)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    async def on_key(self, event: events.Key) -> None:
        if event.key in _APP_KEYS:
            return  # let App-level bindings handle these

        event.stop()

        key = event.key
        char = event.character

        if self.mode == NORMAL:
            self._handle_normal(key, char)
        elif self.mode == INSERT:
            self._handle_insert(key, char)
        elif self.mode == COMMAND:
            self._handle_command(key, char)

        self._adjust_scroll(self.size.height)
        self._post_status()
        self.refresh()

    # ------------------------------------------------------------------
    # Modal handlers
    # ------------------------------------------------------------------

    def _handle_normal(self, key: str, char: str | None) -> None:
        self._status_msg = ""

        if self._pending_d:
            self._pending_d = False
            if char == "d":
                self.buffer.delete_line()
                return

        elif self._pending_g:
            self._pending_g = False
            if char == "g":
                self.buffer.move_to_first_line()
                return

        if key in ("h", "left"):
            self.buffer.move_left()
        elif key in ("j", "down"):
            self.buffer.move_down()
        elif key in ("k", "up"):
            self.buffer.move_up()
        elif key in ("l", "right"):
            self.buffer.move_right(insert_mode=False)
        elif char == "i":
            self.mode = INSERT
        elif char == "I":
            self.buffer.move_to_line_start()
            self.mode = INSERT
        elif char == "a":
            self.buffer.move_right(insert_mode=True)
            self.mode = INSERT
        elif char == "A":
            self.buffer.move_to_line_end(insert_mode=True)
            self.mode = INSERT
        elif char == "o":
            self.buffer.open_line_below()
            self.mode = INSERT
        elif char == "O":
            self.buffer.open_line_above()
            self.mode = INSERT
        elif char == "x":
            self.buffer.delete_char_under()
        elif char == "d":
            self._pending_d = True
        elif char == "g":
            self._pending_g = True
        elif char == "G":
            self.buffer.move_to_last_line()
        elif char == "0":
            self.buffer.move_to_line_start()
        elif char == "$":
            self.buffer.move_to_line_end(insert_mode=False)
        elif char == ":":
            self.mode = COMMAND
            self.command_buf = ""

    def _handle_insert(self, key: str, char: str | None) -> None:
        self._status_msg = ""
        if key == "escape":
            self.mode = NORMAL
            if self.buffer.cursor_x > 0:
                self.buffer.move_left()
            line = self.buffer.lines[self.buffer.cursor_y]
            self.buffer.cursor_x = min(self.buffer.cursor_x, max(len(line) - 1, 0))
        elif key == "backspace":
            self.buffer.delete_char()
        elif key == "enter":
            self.buffer.insert_newline()
        elif key == "tab":
            for _ in range(4):
                self.buffer.insert_char(" ")
        elif key == "up":
            self.buffer.move_up()
        elif key == "down":
            self.buffer.move_down()
        elif key == "left":
            self.buffer.move_left()
        elif key == "right":
            self.buffer.move_right(insert_mode=True)
        elif char is not None and len(char) == 1 and char.isprintable():
            self.buffer.insert_char(char)

    def _handle_command(self, key: str, char: str | None) -> None:
        self._status_msg = ""
        if key == "enter":
            self._execute_command(self.command_buf.strip())
            if self.mode == COMMAND:
                self.mode = NORMAL
                self.command_buf = ""
        elif key == "escape":
            self.mode = NORMAL
            self.command_buf = ""
        elif key == "backspace":
            self.command_buf = self.command_buf[:-1]
        elif char is not None and len(char) == 1 and char.isprintable():
            self.command_buf += char

    def _execute_command(self, cmd: str) -> None:
        if cmd == "w":
            self.save()
        elif cmd == "q":
            if self.buffer.modified:
                self._status_msg = "Unsaved changes -- use :q! to force or :wq to save"
                self.mode = NORMAL
                self.command_buf = ""
            else:
                self.app.exit()
        elif cmd == "q!":
            self.app.exit()
        elif cmd in ("wq", "x"):
            self.save()
            self.app.exit()
        else:
            self._status_msg = f"Unknown command: :{cmd}"
            self.mode = NORMAL
            self.command_buf = ""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _adjust_scroll(self, visible_height: int) -> None:
        visible_height = int(visible_height)
        if visible_height <= 0:
            return
        cy = self.buffer.cursor_y
        if cy < self._scroll_y:
            self._scroll_y = cy
        elif cy >= self._scroll_y + visible_height:
            self._scroll_y = cy - visible_height + 1
        self._scroll_y = max(0, self._scroll_y)

    def _post_status(self) -> None:
        self.post_message(
            self.StatusChanged(
                mode=self.mode,
                filepath=self.filepath,
                cursor_y=self.buffer.cursor_y,
                cursor_x=self.buffer.cursor_x,
                modified=self.buffer.modified,
                command_buf=self.command_buf,
                status_msg=self._status_msg,
            )
        )
