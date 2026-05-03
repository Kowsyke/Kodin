# Kodin - core/editor.py
#
# Editor: owns the curses event loop and the modal state machine.
# Translates raw key codes into buffer mutations and mode transitions.
# Three modes: NORMAL (navigation), INSERT (typing), COMMAND (: commands).
# Delegates all text state to TextBuffer and all drawing to Renderer.

import curses
from core.buffer import TextBuffer
from ui.render import Renderer
from utils.files import load_file, save_file

NORMAL = "NORMAL"
INSERT = "INSERT"
COMMAND = "COMMAND"


class Editor:
    def __init__(self, filepath):
        self.filepath = filepath
        self.buffer = TextBuffer()
        self.mode = NORMAL
        self.command_buf = ""
        self.status_msg = ""
        self._quit = False
        self._pending_d = False  # tracks first 'd' of 'dd' sequence
        self._pending_g = False  # tracks first 'g' of 'gg' sequence

    def start(self):
        lines = load_file(self.filepath)
        self.buffer.load(lines)
        curses.wrapper(self._run)

    def _run(self, stdscr):
        renderer = Renderer(stdscr)
        while not self._quit:
            renderer.draw(
                self.buffer,
                self.mode,
                self.status_msg,
                self.filepath,
                self.command_buf,
            )
            self.status_msg = ""
            key = stdscr.getch()
            self._dispatch(key)

    def _dispatch(self, key):
        if self.mode == NORMAL:
            self._handle_normal(key)
        elif self.mode == INSERT:
            self._handle_insert(key)
        elif self.mode == COMMAND:
            self._handle_command(key)

    def _handle_normal(self, key):
        # --- two-key sequence guards (must be first) ---

        if self._pending_d:
            self._pending_d = False
            if key == ord("d"):
                self.buffer.delete_line()
                return
            # key was not the second 'd': fall through and process it normally

        elif self._pending_g:
            self._pending_g = False
            if key == ord("g"):
                self.buffer.move_to_first_line()
                return
            # key was not the second 'g': fall through and process it normally

        # --- single-key bindings ---

        if key in (ord("h"), curses.KEY_LEFT):
            self.buffer.move_left()
        elif key in (ord("j"), curses.KEY_DOWN):
            self.buffer.move_down()
        elif key in (ord("k"), curses.KEY_UP):
            self.buffer.move_up()
        elif key in (ord("l"), curses.KEY_RIGHT):
            self.buffer.move_right(insert_mode=False)
        elif key == ord("i"):
            self.mode = INSERT
        elif key == ord("I"):
            self.buffer.move_to_line_start()
            self.mode = INSERT
        elif key == ord("a"):
            self.buffer.move_right(insert_mode=True)
            self.mode = INSERT
        elif key == ord("A"):
            self.buffer.move_to_line_end(insert_mode=True)
            self.mode = INSERT
        elif key == ord("o"):
            self.buffer.open_line_below()
            self.mode = INSERT
        elif key == ord("O"):
            self.buffer.open_line_above()
            self.mode = INSERT
        elif key == ord("x"):
            self.buffer.delete_char_under()
        elif key == ord("d"):
            self._pending_d = True
        elif key == ord("g"):
            self._pending_g = True
        elif key == ord("G"):
            self.buffer.move_to_last_line()
        elif key == ord("0"):
            self.buffer.move_to_line_start()
        elif key == ord("$"):
            self.buffer.move_to_line_end(insert_mode=False)
        elif key == ord(":"):
            self.mode = COMMAND
            self.command_buf = ""

    def _handle_insert(self, key):
        if key == 27:  # Escape: back to NORMAL
            self.mode = NORMAL
            if self.buffer.cursor_x > 0:
                self.buffer.move_left()
            # Clamp after the move_left to ensure cursor sits on a real character
            line = self.buffer.lines[self.buffer.cursor_y]
            self.buffer.cursor_x = min(self.buffer.cursor_x, max(len(line) - 1, 0))
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            self.buffer.delete_char()
        elif key in (10, 13):  # Enter
            self.buffer.insert_newline()
        elif key == curses.KEY_UP:
            self.buffer.move_up()
        elif key == curses.KEY_DOWN:
            self.buffer.move_down()
        elif key == curses.KEY_LEFT:
            self.buffer.move_left()
        elif key == curses.KEY_RIGHT:
            self.buffer.move_right(insert_mode=True)
        elif 32 <= key <= 126:  # printable ASCII
            self.buffer.insert_char(chr(key))

    def _handle_command(self, key):
        if key in (10, 13):  # Enter: execute
            self._execute_command(self.command_buf)
            if not self._quit:
                self.mode = NORMAL
                self.command_buf = ""
        elif key == 27:  # Escape: cancel
            self.mode = NORMAL
            self.command_buf = ""
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            self.command_buf = self.command_buf[:-1]
        elif 32 <= key <= 126:
            self.command_buf += chr(key)

    def _execute_command(self, cmd):
        if cmd == "w":
            content = self.buffer.save()
            save_file(self.filepath, content)
            self.status_msg = f"Saved {self.filepath}"
        elif cmd == "q":
            if self.buffer.modified:
                # Only set status_msg here. _handle_command resets mode/command_buf.
                self.status_msg = "Unsaved changes. Use :q! to force quit or :wq to save and quit."
            else:
                self._quit = True
        elif cmd == "q!":
            self._quit = True
        elif cmd == "wq":
            content = self.buffer.save()
            save_file(self.filepath, content)
            self._quit = True
        else:
            self.status_msg = f"Unknown command: :{cmd}"
