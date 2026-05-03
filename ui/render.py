# Kodin - ui/render.py
#
# Renderer: owns the curses screen object and redraws the full terminal
# on every frame. Accepts buffer state as read-only data and never
# modifies it. Responsible for the line number gutter, text area,
# status bar, and cursor placement.

import curses


class Renderer:
    LINE_NUM_WIDTH = 4  # width of the "  1 " gutter prefix

    def __init__(self, stdscr):
        self.stdscr = stdscr
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
        text_width = width - self.LINE_NUM_WIDTH

        lines = buffer.get_lines()
        for screen_y in range(text_height):
            if screen_y < len(lines):
                self._draw_line(screen_y, lines[screen_y], text_width)

        self._draw_status(height, width, mode, filepath, status_msg, command_buf)
        self._place_cursor(buffer.cursor_y, buffer.cursor_x, height, width)
        self.stdscr.refresh()

    def _draw_line(self, y, text, text_width):
        line_num = f"{y + 1:3} "
        try:
            self.stdscr.addstr(y, 0, line_num, curses.color_pair(2))
            self.stdscr.addstr(y, self.LINE_NUM_WIDTH, text[:text_width])
        except curses.error:
            pass  # writing to the last cell of the last row raises; safe to ignore

    def _draw_status(self, height, width, mode, filepath, status_msg, command_buf):
        if mode == "COMMAND":
            bar = f":{command_buf}"
        else:
            bar = f" {mode}  {filepath}"
            if status_msg:
                bar += f"  |  {status_msg}"
        bar = bar[:width - 1].ljust(width - 1)
        try:
            self.stdscr.addstr(height - 1, 0, bar, curses.color_pair(1))
        except curses.error:
            pass

    def _place_cursor(self, cursor_y, cursor_x, height, width):
        screen_y = max(0, min(cursor_y, height - 2))
        screen_x = max(self.LINE_NUM_WIDTH, min(self.LINE_NUM_WIDTH + cursor_x, width - 1))
        self.stdscr.move(screen_y, screen_x)
