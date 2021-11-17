from rich.align import Align
from rich.table import Table

from config import Colors, Layouts
from state import State

class MoveState(State):
    def __init__(self, context):
        super().__init__(context)
        self._cursor_color = Colors.YELLOW.value
        self._key_handlers = {
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

    def _default_handle(self, key):
        pass

    def _go_back(self):
        self._context.change_state("normal")

    def _handle_enter(self):
        self._go_back()

    def _handle_h(self):
        if self._current_tooltip == "initial":
            self._context.sensors.move_sensor(-1, 0)
        else:
            self._default_handle('h')

    def _handle_j(self):
        if self._current_tooltip == "initial":
            self._context.sensors.move_sensor(0, 1)
        else:
            self._default_handle('j')

    def _handle_k(self):
        if self._current_tooltip == "initial":
            self._context.sensors.move_sensor(0, -1)
        else:
            self._default_handle('k')

    def _handle_l(self):
        if self._current_tooltip == "initial":
            self._context.sensors.move_sensor(1, 0)
        else:
            self._default_handle('l')

    def _handle_q_mark(self):
        if self._current_tooltip == "initial":
            layouts = self._context.layouts
            layouts.get(Layouts.DASH.value).visible = False
            layouts.get(Layouts.HELP.value).visible = True
            self._context.change_state("help")
        else:
            self._default_handle('?')

    def on_mount(self):
        self._context.sensors.set_color(self._cursor_color)

    @staticmethod
    def render_initial_tooltip():
        hint = Table(
            box=None,
            title="MOVE MODE",
            show_header=True,
            show_edge=False,
            title_style=f"bold {Colors.YELLOW.value}",
        )
        hint.add_column(justify="center")
        hint.add_row("(◀|h) (▼|j) "
                     "(▲|k) (▶|l) to move")
        hint.add_row("(Enter|q)uit move mode")
        return Align.center(hint, vertical="middle")
