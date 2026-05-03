# Kodin - ui/render.py
#
# Renderer: owns the curses screen object and redraws the full terminal
# on every frame. Accepts buffer state as read-only data and never
# modifies it. Responsible for the line number gutter, text area,
# status bar, cursor placement, and scroll offset tracking.

import curses


class Renderer:

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.scroll_y = 0  # index of the topmost visible line
        self.stdscr.keypad(True)
        curses.raw()
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)  # status bar
        curses.init_pair(2, curses.COLOR_CYAN, -1)                   # line numbers

    def draw(self, buffer, mode, status_msg, filepath, command_buf=""):
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()
        text_height = height - 1  # last row is the status bar

        lines = buffer.get_lines()
        gutter = max(len(str(len(lines))), 3) + 1
        text_width = width - gutter

        self._adjust_scroll(buffer.cursor_y, text_height)

        for screen_y in range(text_height):
            line_idx = self.scroll_y + screen_y
            if line_idx < len(lines):
                self._draw_line(screen_y, line_idx + 1, lines[line_idx], text_width, gutter)
            else:
                try:
                    self.stdscr.addstr(screen_y, 0, "~", curses.A_DIM)
                except curses.error:
                    pass

        self._draw_status(height, width, mode, filepath, status_msg, command_buf, buffer)
        self._place_cursor(buffer.cursor_y, buffer.cursor_x, height, width, gutter)
        self.stdscr.refresh()

    def _adjust_scroll(self, cursor_y, text_height):
        if cursor_y < self.scroll_y:
            self.scroll_y = cursor_y
        elif cursor_y >= self.scroll_y + text_height:
            self.scroll_y = cursor_y - text_height + 1

    def _draw_line(self, y, line_num, text, text_width, gutter):
        num_str = f"{line_num:{gutter - 1}} "
        try:
            self.stdscr.addstr(y, 0, num_str, curses.color_pair(2))
            self.stdscr.addstr(y, gutter, text[:text_width])
        except curses.error:
            pass  # writing to the last cell of the last row raises; safe to ignore

    def _draw_status(self, height, width, mode, filepath, status_msg, command_buf, buffer):
        if mode == "COMMAND":
            bar = f":{command_buf}"
            bar = bar[:width - 1].ljust(width - 1)
        elif status_msg:
            bar = f" {status_msg}"
            bar = bar[:width - 1].ljust(width - 1)
        else:
            modified = " [+]" if buffer.modified else ""
            line_col = f"{buffer.cursor_y + 1}:{buffer.cursor_x + 1} "
            left = f" [{mode}] {filepath}{modified}"
            padding = max(0, width - 1 - len(left) - len(line_col))
            bar = left + " " * padding + line_col
            bar = bar[:width - 1]
        try:
            self.stdscr.addstr(height - 1, 0, bar, curses.color_pair(1))
        except curses.error:
            pass

    def _place_cursor(self, cursor_y, cursor_x, height, width, gutter):
        screen_y = cursor_y - self.scroll_y
        screen_y = max(0, min(screen_y, height - 2))
        screen_x = max(gutter, min(gutter + cursor_x, width - 1))
        self.stdscr.move(screen_y, screen_x)
