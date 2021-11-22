from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Callable, TYPE_CHECKING

from config import Layouts

if TYPE_CHECKING:
    from context import Context
    from rich.console import RenderableType

class State(ABC):
    """The base class for other Thermonitor states

    Args
    ----
        context: thermonitor.Context
            the current Context instance of the process
    """
    def __init__(self, context: Context):
        self._context = context
        self._cursor_color: str|None = None
        self._key_handlers: dict[int|str, Callable[[], None]] = {
            27: self._handle_esc,
            'q': self._handle_q,
        }
        self._current_tooltip = "initial"
        self._previous_state: str|None = None
        self._tooltips: dict[str, Callable[[], RenderableType]] = {
            "initial": self.render_initial_tooltip,
        }

    @abstractmethod
    def _default_handle(self, key: str|int):
        """Abstract method to specify behavior of keys that
        are not handled by other handlers
        """

    def get_context(self) -> Context:
        return self._context

    def get_cursor_color(self) -> str|None:
        return self._cursor_color

    def get_previous_state(self) -> str|None:
        return self._previous_state

    @abstractmethod
    def _go_back(self):
        """Abstract method, specify behavior of back action"""

    def _handle_esc(self):
        """Key handler for abstract _go_back method"""
        self._go_back()

    def handle_key(self, key: str|int):
        """Parent key handler, routes to handler for supplied key"""
        if key in self._key_handlers:
            self._key_handlers[key]()
        else:
            self._default_handle(key)

    def _handle_q(self):
        """Key handler for abstract _go_back method"""
        self._go_back()

    @abstractmethod
    def on_mount(self):
        """Abstract method to specify behavior on transition to state"""

    @staticmethod
    def render_initial_tooltip():
        """Abstract method to display default tooltip in upper right panel"""

    def set_context(self, context: Context):
        """Sets the current application context"""
        self._context = context

    def set_previous_state(self, state: str|None):
        """Sets the name of the previous state, for reference"""
        self._previous_state = state

    def set_tooltip(self, tooltip: str):
        """Sets the name of the current tooltip, used to access dictionary"""
        self._current_tooltip = tooltip
        layout = self._context.layout.get(Layouts.TOOLTIP.value)
        layout.update(self._tooltips[tooltip]())
