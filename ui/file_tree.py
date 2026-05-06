# Kodin - ui/file_tree.py
#
# FileTreePanel: sidebar widget wrapping Textual's DirectoryTree.
# FileSelected messages bubble to KodinApp automatically.

from pathlib import Path

from textual.widget import Widget
from textual.widgets import DirectoryTree, Static
from textual.app import ComposeResult


class FileTreePanel(Widget):

    def compose(self) -> ComposeResult:
        yield Static("  FILES", classes="panel-header")
        yield DirectoryTree(Path.cwd(), id="dir-tree")

    def set_root(self, path: Path) -> None:
        self.query_one("#dir-tree", DirectoryTree).path = path
