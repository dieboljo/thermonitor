from rich.align import Align
from rich.console import Group
from rich.padding import Padding
from rich.table import Table

from config import Colors, Layouts
from state import State

class HelpState(State):

    @staticmethod
    def _any_cell():
        table = Table(box=None, title="GLOBAL COMMANDS", show_header=True,
                      show_edge=False, title_style=f"bold {Colors.CYAN.value}")
        table.add_column()
        table.add_column()
        table.add_column()
        table.add_row(Align.right("h or ◀"), ':', "move cursor right")
        table.add_row(Align.right("l or ▶"), ':', "move cursor right")
        table.add_row(Align.right("k or ▲"), ' :', "move cursor up")
        table.add_row(Align.right("j or ▼"), ' :', "move cursor down")
        table.add_row(Align.right('?'), ' :', "show this help screen")
        return Padding(Align.center(table), 2)

    @staticmethod
    def _command_line_cell():
        table = Table(box=None, title="COMMAND LINE FLAGS", show_header=True,
                      show_edge=False, title_style=f"bold {Colors.GREY.value}")
        table.add_column()
        table.add_column()
        table.add_column()
        table.add_row(Align.right("-f or --file"), ':',
                      "specify state file (defaults to '~/.thermonitor.conf')")
        return Padding(Align.center(table), 2)

    def _default_handle(self, _):
        self._go_back()

    @staticmethod
    def _edit_cell():
        spacing = " " * 3
        table = Table(box=None, title=f"{spacing}EDIT COMMANDS", show_header=True, expand=True,
                      show_edge=False, title_style=f"bold {Colors.RED.value}",
                      title_justify="left")
        table.add_column()
        table.add_column()
        table.add_column()
        table.add_column()
        table.add_row(Align.right('a'), ':', "add a new sensor")
        table.add_row(Align.right('d'), ':', "delete the selected sensor")
        table.add_row(Align.right('r'), ':', "rename the selected sensor")
        table.add_row(Align.right("q, Esc, or Enter"), ':', "go back to normal mode")
        return Padding(Align.left(table), 2)

    def _go_back(self):
        layouts = self._context.layouts
        layouts.get(Layouts.HELP.value).visible = False
        if (self._previous_state == "normal"
                or self._previous_state == "edit"
                or self._previous_state == "move"):
            layouts.get(Layouts.DASH.value).visible = True
        elif self._previous_state == "detail":
            layouts.get(Layouts.DETAIL.value).visible = True
        self._context.change_state(self._previous_state)

    def _modes_cells(self):
        table = Table(box=None, show_header=False,
                      show_edge=False, expand=True)
        table.add_column()
        table.add_column()
        table.add_row(self._normal_cell(), self._edit_cell())
        table.add_row(self._move_cell(), self._timeline_cell())
        return Align.center(table)

    def on_mount(self):
        layout = self._context.layouts.get(Layouts.HELP.value)
        layout.update(Group(Align.center(self._any_cell()),
                            self._modes_cells(),
                            self._command_line_cell()))

    @staticmethod
    def _move_cell():
        spacing = " " * 8
        table = Table(box=None, title=spacing + "MOVE COMMANDS", show_header=True, expand=True,
                      show_edge=False, title_style=f"bold {Colors.YELLOW.value}",
                      title_justify="left")
        table.add_column()
        table.add_column()
        table.add_column()
        table.add_column()
        spacing = " " * 13
        table.add_row(Align.right("q, Esc, or Enter"), ':', "go back to dashboard", spacing)
        return Padding(Align.right(table), 2)

    @staticmethod
    def _normal_cell():
        table = Table(box=None, title="NORMAL COMMANDS", show_header=True, expand=True,
                      show_edge=False, title_style=f"bold {Colors.PURPLE.value}",
                      title_justify="left")
        table.add_column()
        table.add_column()
        table.add_column()
        table.add_row(Align.right('e'), ':', "switch to edit mode")
        table.add_row(Align.right('m'), ':', "switch to move mode")
        table.add_row(Align.right('s'), ':', "save current layout")
        table.add_row(Align.right('t'), ':', "show timeline view")
        table.add_row(Align.right('u'), ':', "toggle temperature units (°C or °F)")
        table.add_row(Align.right("q or Esc"), ':', "quit program")
        return Padding(Align.right(table), 2)

    @staticmethod
    def render_initial_tooltip():
        hint = Table(box=None, title="HELP MODE", show_header=True,
                     show_edge=False, title_style=f"bold {Colors.GREEN.value}")
        hint.add_column()
        hint.add_row("Press any key to return")
        return Align.center(hint, vertical="middle")

    @staticmethod
    def _timeline_cell():
        spacing = " " * 3
        table = Table(box=None, title=f"{spacing}TIMELINE COMMANDS", show_header=True, expand=True,
                      show_edge=False, title_style=f"bold {Colors.PINK.value}",
                      title_justify="left")
        table.add_column()
        table.add_column()
        table.add_column()
        spacing = " " * 6
        table.add_row(spacing, Align.right('m'), ':', "show plot data by minute")
        table.add_row(spacing, Align.right('d'), ':', "show plot data by day")
        table.add_row(spacing, Align.right('h'), ':', "show plot data by hour")
        table.add_row(spacing, Align.right('r'), ':', "refresh plot data")
        table.add_row(spacing, Align.right("q or Esc"), ':', "go back to dashboard")
        return Padding(Align.left(table), 2)
