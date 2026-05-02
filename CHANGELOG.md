# Changelog

All notable changes to Kodin are documented here.

---

## [Unreleased] - Targeting v1.0

### Planned
- curses-based full terminal rendering
- Normal and insert mode
- Real cursor movement (arrow keys + hjkl)
- Character insertion and deletion
- Line splitting on Enter
- :w to save, :q to quit
- Correct edge case handling throughout

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
