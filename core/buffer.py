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

    def move_right(self):
        line_len = len(self.lines[self.cursor_y])
        if self.cursor_x < line_len:
            self.cursor_x += 1
        elif self.cursor_y < len(self.lines) - 1:
            self.cursor_y += 1
            self.cursor_x = 0

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
