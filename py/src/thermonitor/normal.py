"""
NormalState manages Thermonitor's dashboard normal mode.
From this mode, the user can access edit, move, or timeline mode.
In addition, the user can toggle temperatures units and save the
current configuration.
"""
from __future__ import annotations
from typing import Callable, TYPE_CHECKING

from rich.align import Align
from rich.console import RenderableType
from rich.table import Table
from rich.text import Text

from config import Colors, Layouts
from state import State

if TYPE_CHECKING:
    from context import Context

class NormalState(State):
    """Dashboard normal mode

    Args
    ----
        context: thermonitor.Context
            the current Context instance of the process
    """
    def __init__(self, context: Context):
        super().__init__(context)
        self._cursor_color: str = Colors.PURPLE.value
        self._key_handlers: dict[int|str, Callable[[], None]] = {
            27: self._handle_esc,
            63: self._handle_q_mark,
            'a': self._handle_a,
            'd': self._handle_d,
            'e': self._handle_e,
            'h': self._handle_h,
            'j': self._handle_j,
            'k': self._handle_k,
            'l': self._handle_l,
            'm': self._handle_m,
            'n': self._handle_n,
            'p': self._handle_p,
            'q': self._handle_q,
            's': self._handle_s,
            't': self._handle_t,
            'u': self._handle_u,
            'w': self._handle_w,
            'y': self._handle_y,
        }
        self._tooltips: dict[str, Callable[[], RenderableType]] = {
            "initial": self.render_initial_tooltip,
            "save": self.render_save_tooltip,
        }

    def _confirm_save(self):
        """Action to save configuration and revert tooltip to default"""
        self._context.save_config()
        self._go_back()

    def _default_handle(self, _):
        pass

    def _go_back(self):
        """Revert tooltip to default or, if already default, quit application"""
        if self._current_tooltip == "save":
            self.set_tooltip("initial")
        else:
            raise KeyboardInterrupt

    def _handle_e(self):
        """Key handler, enter edit mode"""
        if self._current_tooltip == "initial":
            self._context.change_state("edit")
        else:
            self._default_handle('e')

    def _handle_h(self):
        """Key handler, move cursor left"""
        if self._current_tooltip == "initial":
            self._handle_left()
        else:
            self._default_handle('h')

    def _handle_j(self):
        """Key handler, move cursor down"""
        if self._current_tooltip == "initial":
            self._handle_down()
        else:
            self._default_handle('j')

    def _handle_k(self):
        """Key handler, move cursor up"""
        if self._current_tooltip == "initial":
            self._handle_up()
        else:
            self._default_handle('k')

    def _handle_l(self):
        """Key handler, move cursor right"""
        if self._current_tooltip == "initial":
            self._handle_right()
        else:
            self._default_handle('l')

    def _handle_a(self):
        """Key handler, move cursor left"""
        if self._current_tooltip == "initial":
            self._handle_left()
        else:
            self._default_handle('a')

    def _handle_s(self):
        """Key handler, move cursor down"""
        if self._current_tooltip == "initial":
            self._handle_down()
        else:
            self._default_handle('s')

    def _handle_w(self):
        """Key handler, move cursor up"""
        if self._current_tooltip == "initial":
            self._handle_up()
        else:
            self._default_handle('w')

    def _handle_d(self):
        """Key handler, move cursor right"""
        if self._current_tooltip == "initial":
            self._handle_right()
        else:
            self._default_handle('d')

    def _handle_m(self):
        """Key handler, enter move mode"""
        if self._current_tooltip == "initial":
            self._context.change_state("move")
        else:
            self._default_handle('m')

    def _handle_n(self):
        """Key handler, 'no' response to confirmation prompt"""
        if self._current_tooltip == "save":
            self._go_back()
        else:
            self._default_handle('n')

    def _handle_q_mark(self):
        """Key handler, show help screen"""
        if self._current_tooltip == "initial":
            self._context.change_state("help")
        else:
            self._default_handle('?')

    def _handle_p(self):
        """Key handler, display save (put state) prompt"""
        if self._current_tooltip == "initial":
            self.set_tooltip("save")
        else:
            self._default_handle('p')

    def _handle_t(self):
        """Key handler, enter timeline mode"""
        if self._current_tooltip == "initial":
            self._context.change_state("detail")
        else:
            self._default_handle('t')

    def _handle_u(self):
        """Key handler, toggle temperature units ['C' | 'F']"""
        if self._current_tooltip == "initial":
            self._context.toggle_units()
        else:
            self._default_handle('u')

    def _handle_y(self):
        """Key handler, 'yes' response to confirmation prompt"""
        if self._current_tooltip == "save":
            self._confirm_save()
        else:
            self._default_handle('y')

    def on_mount(self):
        """Change panel border color upon switching to normal mode"""
        self._context.sensors.set_color(self._cursor_color)

    @staticmethod
    def render_initial_tooltip() -> RenderableType:
        """Default tooltip to display in upper right panel"""
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
        hint.add_row("(?)help", "(u)nit", "(p)ut state to file")
        return Align.center(hint, vertical="middle")

    @staticmethod
    def render_save_tooltip() -> RenderableType:
        """Save prompt to display in upper right panel"""
        prompt = Align.left(Text("Save current layout? (y/n)",
                            justify="center",
                            style=f"bold {Colors.GREEN.value}"),
                            vertical="middle")
        return prompt
