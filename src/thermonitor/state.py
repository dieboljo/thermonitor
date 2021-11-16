from abc import ABC, abstractmethod

from config import Layouts


class State(ABC):
    def __init__(self, context):
        self._context = context
        self._cursor_color = None
        self._key_handlers = {
            27: self._handle_esc,
            'q': self._handle_q,
        }
        self._current_tooltip = "initial"
        self._previous_state = None
        self._tooltips = {
            "initial": self.render_initial_tooltip,
        }

    @abstractmethod
    def _default_handle(self, key):
        pass

    def get_context(self):
        return self._context

    def get_cursor_color(self):
        return self._cursor_color

    def get_previous_state(self):
        return self._previous_state

    def get_tooltip(self):
        return self._current_tooltip

    @abstractmethod
    def _go_back(self):
        pass

    def _handle_esc(self):
        self._go_back()

    def handle_key(self, key):
        if key in self._key_handlers:
            self._key_handlers[key]()
        else:
            self._default_handle(key)

    def _handle_q(self):
        self._go_back()

    @abstractmethod
    def on_mount(self):
        pass

    @staticmethod
    def render_initial_tooltip():
        pass

    def set_context(self, context):
        self._context = context

    def set_previous_state(self, state_name):
        self._previous_state = state_name

    def set_tooltip(self, tooltip):
        self._current_tooltip = tooltip
        layout = self._context.get_layouts().get(Layouts.TOOLTIP.value)
        layout.update(self._tooltips[tooltip]())
