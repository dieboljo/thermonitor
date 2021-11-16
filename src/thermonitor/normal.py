from rich.align import Align
from rich.table import Table
from rich.text import Text

from config import Colors, Layouts, Units
from state import State

class NormalState(State):
    def __init__(self, context):
        super().__init__(context)
        self._cursor_color = Colors.PURPLE.value
        self._key_handlers = {
            27: self._handle_esc,
            63: self._handle_q_mark,
            'e': self._handle_e,
            'h': self._handle_h,
            'j': self._handle_j,
            'k': self._handle_k,
            'l': self._handle_l,
            'm': self._handle_m,
            'n': self._handle_n,
            'q': self._handle_q,
            's': self._handle_s,
            't': self._handle_t,
            'u': self._handle_u,
            'y': self._handle_y,
        }
        self._tooltips = {
            "initial": self.render_initial_tooltip,
            "save": self.render_save_tooltip,
        }

    def _confirm_save(self):
        self._context.save_state()
        self._go_back()

    def _default_handle(self, _):
        pass

    def _go_back(self):
        if self._current_tooltip == "save":
            self.set_tooltip("initial")
        else:
            raise KeyboardInterrupt

    def _handle_e(self):
        if self._current_tooltip == "initial":
            self._context.change_state("edit")
        else:
            self._default_handle('e')

    def _handle_h(self):
        if self._current_tooltip == "initial":
            self._context.get_sensors().move_cursor(-1, 0)
        else:
            self._default_handle('h')

    def _handle_j(self):
        if self._current_tooltip == "initial":
            self._context.get_sensors().move_cursor(0, 1)
        else:
            self._default_handle('j')

    def _handle_k(self):
        if self._current_tooltip == "initial":
            self._context.get_sensors().move_cursor(0, -1)
        else:
            self._default_handle('k')

    def _handle_l(self):
        if self._current_tooltip == "initial":
            self._context.get_sensors().move_cursor(1, 0)
        else:
            self._default_handle('l')

    def _handle_m(self):
        if self._current_tooltip == "initial":
            self._context.change_state("move")
        else:
            self._default_handle('m')

    def _handle_n(self):
        if self._current_tooltip == "save":
            self._go_back()
        else:
            self._default_handle('n')

    def _handle_q_mark(self):
        if self._current_tooltip == "initial":
            layouts = self._context.get_layouts()
            layouts.get(Layouts.DASH.value).visible = False
            layouts.get(Layouts.HELP.value).visible = True
            self._context.change_state("help")
        else:
            self._default_handle('?')

    def _handle_s(self):
        if self._current_tooltip == "initial":
            self.set_tooltip("save")
        else:
            self._default_handle('s')

    def _handle_t(self):
        if self._current_tooltip == "initial":
            layouts = self._context.get_layouts()
            layouts.get(Layouts.DASH.value).visible = False
            layouts.get(Layouts.SPINNER.value).visible = True
            self._context.change_state("detail")
        else:
            self._default_handle('t')

    def _handle_u(self):
        if self._current_tooltip == "initial":
            current_unit = self._context.get_unit()
            new_unit = (Units.F.value
                        if current_unit == Units.C.value
                        else Units.C.value)
            self._context.set_unit(new_unit)
            self._context.get_sensors().toggle_units()
        else:
            self._default_handle('u')

    def _handle_y(self):
        if self._current_tooltip == "save":
            self._confirm_save()
        else:
            self._default_handle('y')

    def on_mount(self):
        self._context.get_sensors().set_color(self._cursor_color)

    @staticmethod
    def render_initial_tooltip():
        hint = Table(
            box=None,
            title="NORMAL MODE",
            show_header=True,
            show_edge=False,
            title_style=f"bold {Colors.PURPLE.value}",
        )
        hint.add_column()
        hint.add_column()
        hint.add_column()
        hint.add_row("(t)imeline", "(e)dit mode", "(m)ove mode")
        hint.add_row("(s)ave", "(u)nit toggle", "(?)help")
        return Align.center(hint, vertical="middle")

    @staticmethod
    def render_save_tooltip():
        prompt = Align.left(Text("Save current layout? (y/n)",
                            justify="center"),
                            vertical="middle")
        return prompt
