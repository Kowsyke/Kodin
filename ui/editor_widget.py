# Kodin - ui/editor_widget.py
#
# EditorWidget: the main editing surface. Owns a TextBuffer and implements
# the full NORMAL/INSERT/COMMAND modal state machine. Renders via Rich Text
# with line numbers, cursor highlight, and scroll. Posts StatusChanged on
# every state change so StatusBar stays in sync.

from __future__ import annotations

from textual.widget import Widget
from textual import events
from textual.message import Message
from rich.text import Text
from rich.style import Style

from core.buffer import TextBuffer
from utils.files import load_file, save_file

NORMAL = "NORMAL"
INSERT = "INSERT"
COMMAND = "COMMAND"

# Keys that the App handles globally -- let them pass through this widget.
_APP_KEYS = frozenset({"ctrl+b", "ctrl+t", "ctrl+k", "ctrl+q", "ctrl+s"})


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
    # Rendering
    # ------------------------------------------------------------------

    def render(self) -> Text:
        height = int(self.size.height)
        width = int(self.size.width)

        if height <= 0 or width <= 0:
            return Text("")

        lines = self.buffer.get_lines()
        num_lines = len(lines)
        gutter_w = max(len(str(num_lines)), 3) + 1  # e.g. "  1 " = 4 chars
        text_w = max(width - gutter_w, 1)

        self._adjust_scroll(height)

        cy = self.buffer.cursor_y
        cx = self.buffer.cursor_x

        result = Text(no_wrap=True, overflow="crop")

        for row in range(height):
            if row > 0:
                result.append("\n")

            line_idx = self._scroll_y + row
            is_cursor_row = (line_idx == cy)

            if line_idx < num_lines:
                # --- gutter ---
                num_str = f"{line_idx + 1:>{gutter_w - 1}} "
                gutter_color = "#00d4ff" if is_cursor_row else "#586069"
                result.append(num_str, style=Style(color=gutter_color))

                line = lines[line_idx]

                if is_cursor_row:
                    line_bg = Style(bgcolor="#111827", color="#c9d1d9")
                    cursor_style = Style(bgcolor="#00d4ff", color="#0a0e14", bold=True)

                    # text before cursor
                    before = line[:cx]
                    result.append(before[:text_w], style=line_bg)
                    remaining = text_w - min(len(before), text_w)

                    if remaining > 0:
                        # cursor character
                        cur_ch = line[cx] if cx < len(line) else " "
                        result.append(cur_ch, style=cursor_style)
                        remaining -= 1

                    if remaining > 0:
                        # text after cursor
                        after = line[cx + 1:] if cx < len(line) else ""
                        chunk = after[:remaining]
                        result.append(chunk, style=line_bg)
                        remaining -= len(chunk)

                    if remaining > 0:
                        # pad to end of line so the bg highlight fills the row
                        result.append(" " * remaining, style=line_bg)
                else:
                    result.append(line[:text_w], style=Style(color="#c9d1d9"))

            else:
                # past end of file: tilde rows
                result.append(" " * (gutter_w - 1) + " ", style=Style(color="#586069"))
                result.append("~", style=Style(color="#586069", dim=True))

        return result

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

        # Two-key sequence guards must be checked first.
        if self._pending_d:
            self._pending_d = False
            if char == "d":
                self.buffer.delete_line()
                return
            # Fall through to process the new key normally.

        elif self._pending_g:
            self._pending_g = False
            if char == "g":
                self.buffer.move_to_first_line()
                return

        # Single-key bindings
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
