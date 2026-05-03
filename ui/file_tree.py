# Kodin - ui/file_tree.py
#
# FileTreePanel: sidebar widget wrapping Textual's DirectoryTree.
# Starts at the current working directory. When the user selects a file,
# the DirectoryTree.FileSelected message bubbles up to the App.

from pathlib import Path

from textual.widget import Widget
from textual.widgets import DirectoryTree, Static
from textual.app import ComposeResult


class FileTreePanel(Widget):

    def compose(self) -> ComposeResult:
        yield Static("  FILES", classes="panel-header")
        yield DirectoryTree(Path.cwd(), id="dir-tree")

    def set_root(self, path: Path) -> None:
        """Change the directory tree root (called by app when a file is opened)."""
        tree = self.query_one("#dir-tree", DirectoryTree)
        tree.path = path
