"""
HelpState manages the state of the help screen of the Thermonitor application.
It displays key commands for the program, as well as command line flag options.
"""
from __future__ import annotations

from rich.align import Align
from rich.console import Group, RenderableType
from rich.padding import Padding
from rich.table import Table

from config import Colors, Layouts
from state import State

class HelpState(State):
    """Help screen and its interaction with other screens"""
    @staticmethod
    def _any_cell() -> RenderableType:
        """Grid cell for key commands available in most contexts"""
        table = Table(box=None, title="GLOBAL COMMANDS", show_header=True,
                      show_edge=False, title_style=f"bold {Colors.CYAN.value}")
        table.add_column()
        table.add_column()
        table.add_column()
        table.add_row(Align.right("h or a"), ':', "move cursor left")
        table.add_row(Align.right("l or d"), ':', "move cursor right")
        table.add_row(Align.right("k or w"), ':', "move cursor up")
        table.add_row(Align.right("j or s"), ':', "move cursor down")
        table.add_row(Align.right('?'), ':', "show this help screen")
        return Padding(Align.center(table), 2)

    @staticmethod
    def _command_line_cell() -> RenderableType:
        """Grid cell for command line flags"""
        table = Table(box=None, title="COMMAND LINE FLAGS", show_header=True,
                      show_edge=False, title_style=f"bold {Colors.GREY.value}")
        table.add_column()
        table.add_column()
        table.add_column()
        table.add_row(Align.right("-f or --file"), ':',
                      "specify state file (defaults to '~/.thermonitor.conf')")
        return Padding(Align.center(table), 2)

    def _default_handle(self, _):
        """Key handler for any key"""
        self._go_back()

    @staticmethod
    def _edit_cell() -> RenderableType:
        """Grid cell for key commands in edit mode"""
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
        """Goes back to previous screen"""
        self._context.change_state(self._context.previous_state)

    def _modes_cells(self) -> RenderableType:
        """Grid cell that contains cells of application modes"""
        table = Table(box=None, show_header=False,
                      show_edge=False, expand=True)
        table.add_column()
        table.add_column()
        table.add_row(self._normal_cell(), self._edit_cell())
        table.add_row(self._move_cell(), self._timeline_cell())
        return Align.center(table)

    def on_mount(self):
        """Displays help screen on transition to help state"""
        layout = self._context.layout.get(Layouts.HELP.value)
        layout.update(Group(Align.center(self._any_cell()),
                            self._modes_cells(),
                            self._command_line_cell()))

    @staticmethod
    def _move_cell() -> RenderableType:
        """Grid cell for key commands in move mode"""
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
    def _normal_cell() -> RenderableType:
        """Grid cell for key commands in normal mode"""
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
    def render_initial_tooltip() -> RenderableType:
        """Default tooltip to display in upper right panel"""
        hint = Table(box=None, title="HELP MODE", show_header=True,
                     show_edge=False, title_style=f"bold {Colors.GREEN.value}")
        hint.add_column()
        hint.add_row("Press any key to return")
        return Align.center(hint, vertical="middle")

    @staticmethod
    def _timeline_cell() -> RenderableType:
        """Grid cell for key commands in timeline mode"""
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
        table.add_row(spacing, Align.right('u'), ':', "toggle temperature units (°C or °F)")
        table.add_row(spacing, Align.right("q or Esc"), ':', "go back to dashboard")
        return Padding(Align.left(table), 2)
