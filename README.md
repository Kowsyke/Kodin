# Kodin

A terminal-first code editor, built from scratch in Python.

The name is K + code, after the initial of its creator, Kowshick Ahmed Abir. This is a personal learning project in systems thinking: how text editors actually work at the level of buffers, cursors, terminal rendering, and eventually language server integration.

---

## What It Is Right Now

Kodin is currently at v0.1, which is a working prototype, not a full editor. It can open a file, display its contents with line numbers, let you append new lines, and save. It runs entirely in the terminal using a simple print/input loop.

This is not a finished product. It is a foundation being built deliberately toward v1.0.

---

## Running It

Requires Python 3. No external dependencies.

```bash
python kodin.py yourfile.txt
```

Type text to append new lines to the file. Press Enter on an empty line to save and exit.

---

## The Road to v1.0

v1.0 is the first version of Kodin that works like a real editor:

- Modal editing (normal mode and insert mode)
- Real cursor movement with arrow keys and hjkl
- Character-level insertion and deletion
- File open, save (:w), and quit (:q)
- Full terminal rendering with curses (no scroll flood)
- Stable on edge cases: empty files, long lines, end of buffer

---

## Architecture

The project is organized around clear single responsibilities:

| File | Role |
|------|------|
| `kodin.py` | Entry point only. Boots the editor. |
| `core/editor.py` | Editor loop, mode state machine, command dispatch. |
| `core/buffer.py` | Text storage and cursor tracking. |
| `ui/render.py` | Terminal rendering via curses. |
| `utils/files.py` | File loading and saving. |

---

## Philosophy

Kodin is inspired by Neovim, Helix, and the idea that a text editor is something you can actually understand end to end. The goal is not to replace existing editors but to learn by building one, and eventually have something that reflects how K actually wants to work.

The long-term vision is a programmable hacker-style IDE. The short-term goal is an editor that does not crash.

---

## Creator

Built by Kowshick Ahmed Abir (Kowsyke), CS student, running Fedora 43 with KDE Plasma 6.

Kodin is a learning project and a slow build. It will get there.
