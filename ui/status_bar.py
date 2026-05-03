# Kodin - ui/status_bar.py
#
# StatusBar: a one-line Static widget that listens for StatusChanged messages
# from EditorWidget and renders mode, filepath, modified flag, and line:col.
# Styling is done via Rich markup so the mode block can be colored per-mode.

from textual.widgets import Static
from rich.text import Text
from rich.style import Style


class StatusBar(Static):

    def on_mount(self) -> None:
        self._render_default()

    def _render_default(self) -> None:
        self.update(Text(" [NORMAL]  [new file]", style=Style(bgcolor="#007a94", color="#0a0e14")))

    # Listens for EditorWidget.StatusChanged (bubbles up from EditorWidget)
    def on_editor_widget_status_changed(self, event: object) -> None:
        self.update(self._build(event))

    def _build(self, ev: object) -> Text:
        mode = ev.mode
        filepath = ev.filepath or "[new file]"
        cy = ev.cursor_y + 1
        cx = ev.cursor_x + 1
        modified = ev.modified
        cmd = getattr(ev, "command_buf", "")

        bar = Text(no_wrap=True, overflow="ellipsis")

        if mode == "COMMAND":
            bar.append(f" [COMMAND] ", style=Style(bgcolor="#ff4444", color="#c9d1d9", bold=True))
            bar.append(f":{cmd}", style=Style(bgcolor="#0d1117", color="#c9d1d9"))
        else:
            if mode == "INSERT":
                mode_style = Style(bgcolor="#39d353", color="#0a0e14", bold=True)
            else:
                mode_style = Style(bgcolor="#007a94", color="#0a0e14", bold=True)
            bar.append(f" [{mode}] ", style=mode_style)
            bar.append(f" {filepath}", style=Style(bgcolor="#007a94", color="#0a0e14"))
            if modified:
                bar.append(" [+]", style=Style(bgcolor="#007a94", color="#ff7b00", bold=True))
            line_col = f"  {cy}:{cx} "
            bar.append(line_col, style=Style(bgcolor="#007a94", color="#0a0e14"))

        return bar
