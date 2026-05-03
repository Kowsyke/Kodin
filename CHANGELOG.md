# Changelog

All notable changes to Kodin are documented here.

---

## [Unreleased] - Targeting v1.0

### Planned
- Scroll offset for files longer than the terminal height
- Syntax highlighting
- Line count in status bar
- Search with /

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
