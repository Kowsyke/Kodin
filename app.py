# Kodin - app.py
#
# KodinApp: Textual application root. Owns the layout and top-level bindings.
# All editing logic lives in EditorWidget. This file only wires things together.

from __future__ import annotations

import sys
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import DirectoryTree

from ui.editor_widget import EditorWidget
from ui.file_tree import FileTreePanel
from ui.claude_panel import ClaudePanel
from ui.terminal_panel import TerminalPanel
from ui.status_bar import StatusBar


class KodinApp(App):
    CSS_PATH = str(Path(__file__).parent / "kodin.tcss")
    TITLE = "Kodin"

    BINDINGS = [
        Binding("ctrl+b", "toggle_sidebar", "Sidebar", show=False),
        Binding("ctrl+t", "toggle_terminal", "Terminal", show=False),
        Binding("ctrl+k", "toggle_claude", "Claude", show=False),
        Binding("ctrl+q", "quit", "Quit", show=False),
        Binding("ctrl+s", "save", "Save", show=False),
    ]

    def __init__(self, filepath: str | None = None) -> None:
        super().__init__()
        self._filepath = filepath

    def compose(self) -> ComposeResult:
        yield Horizontal(
            FileTreePanel(id="sidebar"),
            Vertical(
                Horizontal(
                    EditorWidget(id="editor"),
                    ClaudePanel(id="claude-panel"),
                    id="editor-row",
                ),
                TerminalPanel(id="terminal-panel"),
                StatusBar(id="status-bar"),
                id="main-content",
            ),
            id="root-split",
        )

    def on_mount(self) -> None:
        editor = self.query_one("#editor", EditorWidget)
        if self._filepath:
            try:
                editor.load_file(self._filepath)
                self.sub_title = self._filepath
                self.query_one("#sidebar", FileTreePanel).set_root(
                    Path(self._filepath).parent
                )
            except Exception as exc:
                editor._status_msg = f"Could not open: {exc}"
                editor._post_status()
        else:
            self.sub_title = "[new file]"
        editor.focus()

    # ------------------------------------------------------------------
    # Actions (bound to ctrl+* keys above)
    # ------------------------------------------------------------------

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar", FileTreePanel)
        sidebar.display = not sidebar.display

    def action_toggle_terminal(self) -> None:
        panel = self.query_one("#terminal-panel", TerminalPanel)
        panel.display = not panel.display
        if panel.display:
            panel.focus()
        else:
            self.query_one("#editor", EditorWidget).focus()

    def action_toggle_claude(self) -> None:
        panel = self.query_one("#claude-panel", ClaudePanel)
        panel.display = not panel.display
        if panel.display:
            editor = self.query_one("#editor", EditorWidget)
            panel.set_context(editor.get_selected_text())

    def action_save(self) -> None:
        editor = self.query_one("#editor", EditorWidget)
        editor.save()
        editor._post_status()
        editor.refresh()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = str(event.path)
        editor = self.query_one("#editor", EditorWidget)
        editor.load_file(path)
        self.sub_title = path
        self.query_one("#terminal-panel", TerminalPanel).set_cwd(path)
