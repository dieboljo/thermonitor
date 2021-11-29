"""
MoveState manages Thermonitor's dashboard state when in move mode.
Cursor keys move the sensor that is selected on entry into the mode.
"""
from __future__ import annotations
from typing import Callable, TYPE_CHECKING

from rich.align import Align
from rich.console import RenderableType
from rich.table import Table

from config import Colors, Layouts
from state import State

if TYPE_CHECKING:
    from context import Context

class MoveState(State):
    """Dashboard move mode

    Args
    ----
        context: thermonitor.Context
            the current Context instance of the process
    """
    def __init__(self, context: Context):
        super().__init__(context)
        self._cursor_color: str = Colors.YELLOW.value
        self._key_handlers: dict[int|str, Callable[[], None]] = {
            10: self._handle_enter,
            27: self._handle_esc,
            63: self._handle_q_mark,
            'h': self._handle_h,
            'j': self._handle_j,
            'k': self._handle_k,
            'l': self._handle_l,
            'q': self._handle_q,
        }
        self._tooltips = {
            "initial": self.render_initial_tooltip,
        }

    def _default_handle(self, _):
        pass

    def _go_back(self):
        """Returns to normal mode"""
        self._context.change_state("normal")

    def _handle_enter(self):
        """Key handler, return to normal mode"""
        self._go_back()

    def _handle_h(self):
        """Key handler, move cursor left"""
        if self._current_tooltip == "initial":
            self._context.sensors.move_sensor(-1, 0)
        else:
            self._default_handle('h')

    def _handle_j(self):
        """Key handler, move cursor down"""
        if self._current_tooltip == "initial":
            self._context.sensors.move_sensor(0, 1)
        else:
            self._default_handle('j')

    def _handle_k(self):
        """Key handler, move cursor up"""
        if self._current_tooltip == "initial":
            self._context.sensors.move_sensor(0, -1)
        else:
            self._default_handle('k')

    def _handle_l(self):
        """Key handler, move cursor right"""
        if self._current_tooltip == "initial":
            self._context.sensors.move_sensor(1, 0)
        else:
            self._default_handle('l')

    def _handle_q_mark(self):
        """Key handler, show help screen"""
        if self._current_tooltip == "initial":
            layout = self._context.layout
            layout.get(Layouts.DASH.value).visible = False
            layout.get(Layouts.HELP.value).visible = True
            self._context.change_state("help")
        else:
            self._default_handle('?')

    def on_mount(self):
        """Change panel border color upon switching to move mode"""
        self._context.sensors.set_color(self._cursor_color)

    @staticmethod
    def render_initial_tooltip() -> RenderableType:
        """Default tooltip to display in upper right panel"""
        hint = Table(
            box=None,
            title="MOVE MODE",
            show_header=True,
            show_edge=False,
            title_style=f"bold {Colors.YELLOW.value}",
        )
        hint.add_column(justify="center")
        hint.add_row("(◀|h)  (▼|j)  "
                     "(▲|k)  (▶|l)")
        hint.add_row("(Enter|q)uit move mode")
        return Align.center(hint, vertical="middle")