# Kodin - ui/status_bar.py
#
# StatusBar: one-line widget that listens for StatusChanged messages and
# renders mode block, filepath, modified flag, and line:col.

from textual.widgets import Static
from rich.text import Text
from rich.style import Style

from ui.editor_widget import EditorWidget


class StatusBar(Static):

    def on_mount(self) -> None:
        self.update(self._default())

    def on_editor_widget_status_changed(self, event: EditorWidget.StatusChanged) -> None:
        self.update(self._build(event))

    def _default(self) -> Text:
        t = Text(no_wrap=True, overflow="ellipsis")
        t.append(" NORMAL ", style=Style(bgcolor="#007a94", color="#0a0e14", bold=True))
        t.append("  [new file]", style=Style(bgcolor="#007a94", color="#0a0e14"))
        return t

    def _build(self, ev: EditorWidget.StatusChanged) -> Text:
        mode = ev.mode
        # Use status_msg as filepath display when present (transient messages)
        filepath = ev.status_msg if ev.status_msg else (ev.filepath or "[new file]")
        cy = ev.cursor_y + 1
        cx = ev.cursor_x + 1
        modified = ev.modified
        cmd = ev.command_buf

        t = Text(no_wrap=True, overflow="ellipsis")

        if mode == "COMMAND":
            t.append(" COMMAND ", style=Style(bgcolor="#ff4444", color="#c9d1d9", bold=True))
            t.append(f" :{cmd}", style=Style(bgcolor="#0d1117", color="#c9d1d9"))
        else:
            if mode == "INSERT":
                mode_style = Style(bgcolor="#39d353", color="#0a0e14", bold=True)
            else:
                mode_style = Style(bgcolor="#007a94", color="#0a0e14", bold=True)

            t.append(f" {mode} ", style=mode_style)
            t.append(f"  {filepath}", style=Style(bgcolor="#007a94", color="#0a0e14"))
            if modified:
                t.append(" [+]", style=Style(bgcolor="#007a94", color="#ff7b00", bold=True))
            t.append(f"  {cy}:{cx} ", style=Style(bgcolor="#007a94", color="#0a0e14"))

        return t
