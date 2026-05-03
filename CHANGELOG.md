# Changelog

All notable changes to Kodin are documented here.

---

## [Unreleased] - Targeting v1.0

### Planned
- Syntax highlighting (Python first, via regex)
- Search with /
- Word-level movement: w, b, e
- Relative line numbers in gutter

---

## [0.4] - 2026-05-03

### Changed
- Replaced the entire curses stack with Textual 8.2.5. `core/editor.py` and
  `ui/render.py` are deleted; all rendering, input handling, and layout now live
  in Textual widgets.
- `kodin.py` is now four lines: creates `KodinApp` and calls `.run()`.
- `core/buffer.py` and `utils/files.py` are unchanged.

### Added
- `app.py`: `KodinApp(App)` with five global bindings (ctrl+b/t/k/q/s) and a
  three-panel layout: sidebar / editor-row / terminal / status-bar.
- `ui/editor_widget.py`: `EditorWidget(Widget)` with full NORMAL/INSERT/COMMAND
  modal editing, all v0.3 vim bindings, Rich Text rendering with neon-cyan cursor
  and line highlight, scroll management, and a `StatusChanged` message.
- `ui/file_tree.py`: `FileTreePanel(Widget)` wrapping Textual `DirectoryTree`.
  Selecting a file loads it into the editor.
- `ui/status_bar.py`: `StatusBar(Static)` listening for `StatusChanged` messages.
  Renders mode block in color (cyan/green/red per mode), filename, `[+]` in orange,
  and `line:col`.
- `ui/claude_panel.py`: `ClaudePanel(Widget)` with `RichLog`, `Input`, and `Button`.
  Streams responses from `claude-sonnet-4-6` via the Anthropic SDK using
  `@work(thread=True)`. Conversation history capped at 20 messages. Toggle with ctrl+k.
- `ui/terminal_panel.py`: `TerminalPanel(Widget)` with a real pty subprocess shell.
  Output streamed via `@work(thread=True)` into `RichLog`. Keyboard input forwarded
  to the pty. Toggle with ctrl+t.
- `kodin.tcss`: full dark hacker aesthetic. Neon cyan accent, near-black background,
  all layout sizing in CSS variables.
- `requirements.txt`: `textual>=8.2.5`, `anthropic>=0.25.0`.

---

## [0.3] - 2026-05-03

### Fixed (utils/files.py)
- `load_file` now returns `[""]` on `FileNotFoundError` instead of `[]`, so
  opening a nonexistent file starts a blank buffer instead of crashing.
- `save_file` now appends a trailing newline to all saved files (POSIX compliance).
  The fix lives in `save_file`, not in `buffer.save()`, which stays pure.

### Fixed (core/buffer.py)
- `move_right()` gains an `insert_mode=False` parameter. In NORMAL mode the cursor
  can no longer sit past the last character of a line; it clamps to `len(line) - 1`.
  INSERT mode and the 'a' binding pass `insert_mode=True` to allow the cursor after
  the last character.
- The 'o' (open line below) binding no longer directly mutates `buffer.cursor_x`
  from the editor. A new `open_line_below()` method encapsulates the operation.
- `_execute_command(':q')` no longer sets `self.mode` or `self.command_buf`; those
  are now managed entirely by `_handle_command()`, removing a fragile double-write.
- ESC from INSERT mode now explicitly clamps `cursor_x` to the last valid NORMAL
  mode position after the move_left call.

### Added (core/buffer.py)
- `delete_char_under()`: deletes the character at the cursor (vim 'x'); clamps
  cursor after deletion.
- `delete_line()`: deletes the entire current line (vim 'dd'); preserves a minimum
  of one line in the buffer.
- `open_line_below()`: inserts a blank line below the current line (vim 'o').
- `open_line_above()`: inserts a blank line above the current line (vim 'O').
- `move_to_line_start()`: sets cursor_x to 0 (vim '0').
- `move_to_line_end(insert_mode=False)`: moves cursor to last char (NORMAL) or one
  past it (INSERT); covers vim '$' and 'A'.
- `move_to_first_line()`: jumps to line 0 (vim 'gg').
- `move_to_last_line()`: jumps to last line (vim 'G').
- `_clamp_x()`: private helper used by jump and delete operations to keep
  cursor_x in valid NORMAL mode range.

### Fixed (ui/render.py)
- Critical scroll bug: the renderer now tracks `scroll_y` (topmost visible line)
  and calls `_adjust_scroll()` before every draw. Files of any length now display
  and scroll correctly without curses errors.
- Gutter width is now computed dynamically from `len(str(num_lines))` instead of
  hardcoded to 4; files with 1000+ lines no longer overflow the gutter.
- Tilde (`~`) rows are shown for screen rows past the end of the file (like vim).
- Status bar now shows `[MODE] filename [+]` left-aligned and `line:col`
  right-aligned. `[+]` appears only when the buffer has unsaved changes.

### Added (core/editor.py)
- NORMAL mode bindings: `x` (delete char under), `dd` (delete line), `0` (line
  start), `$` (line end), `A` (append at end, enter INSERT), `I` (insert at start,
  enter INSERT), `O` (open line above, enter INSERT), `G` (last line), `gg` (first
  line).
- Two-key sequence state: `_pending_d` for `dd` and `_pending_g` for `gg`. Handles
  the "other key resets and processes normally" edge case.

---

## [0.2] - 2026-05-03

### Changed
- Rewrote `core/buffer.py`: TextBuffer now owns `cursor_y`, `cursor_x`, and a
  `modified` flag. Full character-level mutation API: `insert_char`, `delete_char`
  (with line-merge on backspace at column 0), `insert_newline` (line-split at cursor),
  and all four directional movement methods with correct clamping.
- Rewrote `ui/render.py` as a `Renderer` class using curses. Draws a line number
  gutter, text content, and a status bar showing the current mode and filename.
  Positions the real terminal cursor on every frame.
- Rewrote `core/editor.py` with a `curses.wrapper` event loop and a three-mode
  state machine: NORMAL, INSERT, and COMMAND.
- Simplified `kodin.py` to a 16-line entry point. All inline loop logic removed.

### Added
- NORMAL mode navigation: hjkl and arrow keys, `i` (insert before), `a` (insert
  after), `o` (open new line below), `:` to enter COMMAND mode.
- INSERT mode: printable character insertion, Backspace with line-merge, Enter with
  line-split, arrow keys, Escape to return to NORMAL.
- COMMAND mode: `:w` save, `:q` quit with unsaved-changes warning, `:q!` force
  quit, `:wq` save and quit.
- File header comments on every module explaining its single responsibility.
- `tests/test_buffer.py`: 27 unit tests covering all TextBuffer behavior (TDD).
- `tests/test_files.py`: 5 unit tests for load_file and save_file.

### Fixed
- Removed the accidentally committed `utils/__pycache__/files.cpython-314.pyc`.
- `cursor_x` is now clamped to line length on all movement operations.
- Empty file now initializes to one blank line with cursor at (0, 0).

---

## [0.1] - 2026-03-06

### Added
- Project scaffolded: kodin.py, core/editor.py, core/buffer.py, ui/render.py, utils/files.py
- File loading via `utils/files.py` (load_file, save_file)
- TextBuffer class in core/buffer.py with load, append, get_lines, save
- Basic display function in ui/render.py that prints numbered lines
- Editor class in core/editor.py with :w and :q command handling
- Append mode: user can type new lines and they are added to the buffer
- hjkl key tracking in kodin.py (position variables, not real cursor movement)
- docs/kodin_project_context.json with project philosophy and roadmap

### Known Issues
- kodin.py does not use the Editor class; it has its own inline loop
- core/editor.py is dead code in this state
- No curses; rendering is done entirely via print() and input()
- TextBuffer cannot insert or delete, only append
- Cursor position is tracked as a variable but has no effect on the terminal
- utils/__pycache__/files.cpython-314.pyc committed accidentally
