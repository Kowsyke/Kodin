# Kodin - ui/editor_widget.py
#
# EditorWidget: the main editing surface. Owns a TextBuffer and implements
# the full NORMAL/INSERT/COMMAND modal state machine from v0.3. Renders via
# Rich Text (line numbers, cursor highlight, tilde rows). Posts StatusChanged
# on every state change so the StatusBar stays in sync.

from __future__ import annotations

from textual.widget import Widget
from textual.app import ComposeResult
from textual import events
from textual.message import Message
from rich.text import Text
from rich.style import Style

from core.buffer import TextBuffer
from utils.files import load_file, save_file

NORMAL = "NORMAL"
INSERT = "INSERT"
COMMAND = "COMMAND"

# Keys the App handles at the global level; EditorWidget lets them pass through.
_APP_KEYS = frozenset({"ctrl+b", "ctrl+t", "ctrl+k", "ctrl+q", "ctrl+s"})


class EditorWidget(Widget):
    """Modal vim-style editor surface backed by TextBuffer."""

    can_focus = True

    # --- nested message ---

    class StatusChanged(Message):
        """Posted whenever mode, cursor, or modified state changes."""
        def __init__(
            self,
            mode: str,
            filepath: str,
            cursor_y: int,
            cursor_x: int,
            modified: bool,
            command_buf: str = "",
        ) -> None:
            super().__init__()
            self.mode = mode
            self.filepath = filepath
            self.cursor_y = cursor_y
            self.cursor_x = cursor_x
            self.modified = modified
            self.command_buf = command_buf

    # --- lifecycle ---

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.buffer = TextBuffer()
        self.filepath: str = ""
        self.mode: str = NORMAL
        self.command_buf: str = ""
        self.scroll_y: int = 0
        self._pending_d: bool = False
        self._pending_g: bool = False
        self._status_msg: str = ""

    def on_mount(self) -> None:
        self._post_status()

    # --- public API ---

    def load_file(self, path: str) -> None:
        self.filepath = path
        lines = load_file(path)
        self.buffer.load(lines)
        self.scroll_y = 0
        self.mode = NORMAL
        self.command_buf = ""
        self._status_msg = ""
        self._post_status()
        self.refresh()

    def save(self) -> None:
        if not self.filepath:
            self._status_msg = "No filename. Use :w <name> to save."
            self._post_status()
            self.refresh()
            return
        content = self.buffer.save()
        save_file(self.filepath, content)
        self._status_msg = f"Saved {self.filepath}"
        self._post_status()
        self.refresh()

    def get_selected_text(self) -> str:
        """Return the current line for use as Claude context."""
        return self.buffer.lines[self.buffer.cursor_y]

    # --- rendering ---

    def render(self) -> Text:
        height = self.size.height
        width = self.size.width

        if height <= 0 or width <= 0:
            return Text("")

        lines = self.buffer.get_lines()
        num_lines = len(lines)
        gutter = max(len(str(num_lines)), 3) + 1
        text_width = max(width - gutter, 1)

        self._adjust_scroll(height)

        cy = self.buffer.cursor_y
        cx = self.buffer.cursor_x

        result = Text(no_wrap=True, overflow="crop")

        for row in range(height):
            line_idx = self.scroll_y + row
            is_cursor = line_idx == cy

            if row > 0:
                result.append("\n")

            if line_idx < num_lines:
                num_str = f"{line_idx + 1:>{gutter - 1}} "
                gutter_color = "#007a94" if is_cursor else "#586069"
                result.append(num_str, style=Style(color=gutter_color))

                line = lines[line_idx]

                if is_cursor:
                    bg = Style(bgcolor="#111827", color="#c9d1d9")
                    cur_style = Style(bgcolor="#00d4ff", color="#0a0e14", bold=True)

                    before = line[:cx][:text_width]
                    remaining = text_width - len(before)

                    result.append(before, style=bg)

                    if remaining > 0:
                        cursor_char = line[cx] if cx < len(line) else " "
                        result.append(cursor_char, style=cur_style)
                        remaining -= 1

                    if remaining > 0:
                        after = line[cx + 1:] if cx < len(line) else ""
                        result.append(after[:remaining], style=bg)
                        remaining -= len(after[:remaining])

                    if remaining > 0:
                        result.append(" " * remaining, style=bg)
                else:
                    result.append(line[:text_width], style=Style(color="#c9d1d9"))
            else:
                result.append(" " * (gutter - 1) + " ", style=Style(color="#586069"))
                result.append("~", style=Style(color="#586069", dim=True))

        return result

    # --- key handling ---

    async def on_key(self, event: events.Key) -> None:
        if event.key in _APP_KEYS:
            return  # let App bindings fire

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

    def _handle_normal(self, key: str, char: str | None) -> None:
        self._status_msg = ""

        # Two-key sequence guards must come first
        if self._pending_d:
            self._pending_d = False
            if char == "d":
                self.buffer.delete_line()
                return
            # Not the second 'd': fall through and process this key normally

        elif self._pending_g:
            self._pending_g = False
            if char == "g":
                self.buffer.move_to_first_line()
                return
            # Not the second 'g': fall through

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
        if key == "enter":
            self._execute_command(self.command_buf)
            if self.mode == COMMAND:  # not cleared by _execute_command exit path
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
                self._status_msg = "Unsaved changes. Use :q! to force quit or :wq to save and quit."
                self.mode = NORMAL
                self.command_buf = ""
            else:
                self.app.exit()
        elif cmd == "q!":
            self.app.exit()
        elif cmd == "wq":
            self.save()
            self.app.exit()
        else:
            self._status_msg = f"Unknown command: :{cmd}"
            self.mode = NORMAL
            self.command_buf = ""

    # --- helpers ---

    def _adjust_scroll(self, visible_height: int) -> None:
        if visible_height <= 0:
            return
        cy = self.buffer.cursor_y
        if cy < self.scroll_y:
            self.scroll_y = cy
        elif cy >= self.scroll_y + visible_height:
            self.scroll_y = cy - visible_height + 1
        self.scroll_y = max(0, self.scroll_y)

    def _post_status(self) -> None:
        # If there is a transient status message, show it as filepath override
        fp = self._status_msg if self._status_msg else self.filepath
        self.post_message(
            self.StatusChanged(
                mode=self.mode,
                filepath=fp,
                cursor_y=self.buffer.cursor_y,
                cursor_x=self.buffer.cursor_x,
                modified=self.buffer.modified,
                command_buf=self.command_buf,
            )
        )
