# Kodin - core/buffer.py
#
# Text buffer: stores all editor content as a list of strings (no trailing
# newlines), owns cursor position (cursor_y, cursor_x), and exposes every
# mutation the editor needs. No I/O, no terminal interaction of any kind.

class TextBuffer:
    def __init__(self):
        self.lines = [""]
        self.cursor_y = 0
        self.cursor_x = 0
        self.modified = False

    def load(self, lines):
        self.lines = list(lines) if lines else [""]
        self.cursor_y = 0
        self.cursor_x = 0
        self.modified = False

    def get_lines(self):
        return self.lines

    def save(self):
        self.modified = False
        return "\n".join(self.lines)

    # --- cursor movement ---

    def move_up(self):
        if self.cursor_y > 0:
            self.cursor_y -= 1
            self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))

    def move_down(self):
        if self.cursor_y < len(self.lines) - 1:
            self.cursor_y += 1
            self.cursor_x = min(self.cursor_x, len(self.lines[self.cursor_y]))

    def move_left(self):
        if self.cursor_x > 0:
            self.cursor_x -= 1
        elif self.cursor_y > 0:
            self.cursor_y -= 1
            self.cursor_x = len(self.lines[self.cursor_y])

    def move_right(self, insert_mode=False):
        line_len = len(self.lines[self.cursor_y])
        if self.cursor_x < line_len:
            self.cursor_x += 1
        elif self.cursor_y < len(self.lines) - 1:
            self.cursor_y += 1
            self.cursor_x = 0
        if not insert_mode:
            self._clamp_x()

    # --- mutations ---

    def insert_char(self, ch):
        line = self.lines[self.cursor_y]
        self.lines[self.cursor_y] = line[:self.cursor_x] + ch + line[self.cursor_x:]
        self.cursor_x += 1
        self.modified = True

    def delete_char(self):
        """Backspace: delete the character before the cursor, or merge lines."""
        if self.cursor_x > 0:
            line = self.lines[self.cursor_y]
            self.lines[self.cursor_y] = line[:self.cursor_x - 1] + line[self.cursor_x:]
            self.cursor_x -= 1
            self.modified = True
        elif self.cursor_y > 0:
            prev = self.lines[self.cursor_y - 1]
            curr = self.lines[self.cursor_y]
            new_x = len(prev)
            self.lines[self.cursor_y - 1] = prev + curr
            del self.lines[self.cursor_y]
            self.cursor_y -= 1
            self.cursor_x = new_x
            self.modified = True

    def insert_newline(self):
        line = self.lines[self.cursor_y]
        self.lines[self.cursor_y] = line[:self.cursor_x]
        self.lines.insert(self.cursor_y + 1, line[self.cursor_x:])
        self.cursor_y += 1
        self.cursor_x = 0
        self.modified = True

    # --- vim-style operations ---

    def delete_char_under(self):
        """Delete the character at cursor_x (vim 'x'). No-op on empty line."""
        line = self.lines[self.cursor_y]
        if self.cursor_x >= len(line):
            return
        self.lines[self.cursor_y] = line[:self.cursor_x] + line[self.cursor_x + 1:]
        self._clamp_x()
        self.modified = True

    def delete_line(self):
        """Delete the entire current line (vim 'dd'). Buffer always keeps one line."""
        if len(self.lines) == 1:
            self.lines[0] = ""
        else:
            del self.lines[self.cursor_y]
            self.cursor_y = min(self.cursor_y, len(self.lines) - 1)
        self._clamp_x()
        self.modified = True

    def open_line_below(self):
        """Insert a blank line below the current line and move cursor there."""
        self.cursor_x = len(self.lines[self.cursor_y])
        self.insert_newline()

    def open_line_above(self):
        """Insert a blank line above the current line and move cursor there."""
        self.lines.insert(self.cursor_y, "")
        self.cursor_x = 0
        self.modified = True

    # --- jump navigation ---

    def move_to_line_start(self):
        """Move to column 0 (vim '0')."""
        self.cursor_x = 0

    def move_to_line_end(self, insert_mode=False):
        """Move to end of line. NORMAL mode: last char. INSERT mode: past last char (vim '$'/'A')."""
        if insert_mode:
            self.cursor_x = len(self.lines[self.cursor_y])
        else:
            self.cursor_x = max(len(self.lines[self.cursor_y]) - 1, 0)

    def move_to_first_line(self):
        """Jump to line 0 (vim 'gg')."""
        self.cursor_y = 0
        self._clamp_x()

    def move_to_last_line(self):
        """Jump to last line (vim 'G')."""
        self.cursor_y = len(self.lines) - 1
        self._clamp_x()

    # --- private helpers ---

    def _clamp_x(self):
        """Clamp cursor_x to valid NORMAL mode range for the current line."""
        self.cursor_x = min(self.cursor_x, max(len(self.lines[self.cursor_y]) - 1, 0))
