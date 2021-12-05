"""
EditState manages Thermonitor's dashboard state when in
edit mode. Allows for adding, deleting, and renaming sensors.
"""
from __future__ import annotations
from typing import Callable, TYPE_CHECKING

from rich.align import Align
from rich.console import RenderableType
from rich.table import Table
from rich.text import Text

from config import Colors, Layouts
from input import Input
from state import State

if TYPE_CHECKING:
    from context import Context

class EditState(State):
    """Dashboard edit mode"""
    VALID_ID_CHARS = "abcdefghijklmnopqrstuvwxyz1234567890"
    VALID_LABEL_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'-"
    ID_WARNINGS = ["blank_id", "duplicate_id"]

    def __init__(self, context: Context):
        super().__init__(context)
        self._cursor_color: str = Colors.RED.value
        self._key_handlers: dict[int|str, Callable[[], None]] = {
            27: self._handle_esc,
            63: self._handle_q_mark,
            127: self._handle_backspace,
            10: self._handle_enter,
            ' ': self._handle_space,
            'a': self._handle_a,
            'c': self._handle_c,
            'd': self._handle_d,
            'h': self._handle_h,
            'j': self._handle_j,
            'k': self._handle_k,
            'l': self._handle_l,
            'n': self._handle_n,
            'q': self._handle_q,
            'r': self._handle_r,
            's': self._handle_s,
            'w': self._handle_w,
            'y': self._handle_y,
        }
        self._tooltips: dict[str, Callable[[], RenderableType]] = {
            "blank_id": self._render_blank_id_tooltip,
            "delete": self._render_delete_tooltip,
            "duplicate_id": self._render_duplicate_id_tooltip,
            "id_prompt": self._render_id_prompt_tooltip,
            "initial": self._render_initial_tooltip,
            "label_prompt": self._render_label_prompt_tooltip,
            "rename_prompt": self._render_rename_prompt_tooltip,
        }
        self._id_input = Input(self.VALID_ID_CHARS)
        self._label_input = Input(self.VALID_LABEL_CHARS)
        self._rename_input = Input(self.VALID_LABEL_CHARS)

    def _confirm_delete(self):
        self._context.sensors.remove_sensor()
        self._go_back()

    def _default_handle(self, key: int|str):
        """Key handler, handles keys without special functions
        or keys pressed when prompt is displayed
        """
        if self._current_tooltip in self.ID_WARNINGS:
            self._go_back()
        elif isinstance(key, str):
            if self._current_tooltip == "label_prompt":
                self._label_input.append_clean(key)
                self.set_tooltip("label_prompt")
            elif self._current_tooltip == "id_prompt":
                self._id_input.append_clean(key)
                self.set_tooltip("id_prompt")
            elif self._current_tooltip == "rename_prompt":
                self._rename_input.append_clean(key)
                self.set_tooltip("rename_prompt")

    def _go_back(self):
        """Returns to normal dashboard mode"""
        if self._current_tooltip == "delete":
            self.set_tooltip("initial")
        elif self._current_tooltip == "label_prompt":
            self._label_input.reset()
            self.set_tooltip("initial")
        elif self._current_tooltip == "id_prompt":
            self._label_input.reset()
            self._id_input.reset()
            self.set_tooltip("initial")
        elif self._current_tooltip in self.ID_WARNINGS:
            self._id_input.reset()
            self.set_tooltip("id_prompt")
        elif self._current_tooltip == "rename_prompt":
            self._rename_input.reset()
            self.set_tooltip("initial")
        else:
            self._context.change_state("normal")

    def _handle_backspace(self):
        """Key handler for input prompts"""
        if self._current_tooltip == "label_prompt":
            self._label_input.pop()
            self.set_tooltip("label_prompt")
        elif self._current_tooltip == "id_prompt":
            self._id_input.pop()
            self.set_tooltip("id_prompt")
        elif self._current_tooltip == "rename_prompt":
            self._rename_input.pop()
            self.set_tooltip("rename_prompt")
        else:
            self._default_handle(127)

    def _handle_r(self):
        """Key handler, signals intent to remove sensor from dashboard"""
        if self._current_tooltip == "initial":
            self.set_tooltip("delete")
        else:
            self._default_handle('r')

    def _handle_enter(self):
        """Key handler, submits input or returns to normal mode"""
        if self._current_tooltip == "label_prompt":
            self.set_tooltip("id_prompt")
        elif self._current_tooltip == "id_prompt":
            self._submit_create()
        elif self._current_tooltip == "rename_prompt":
            self._submit_rename()
        elif self._current_tooltip == "initial":
            self._go_back()
        else:
            self._default_handle(10)

    def _handle_h(self):
        """Key handler, moves cursor left"""
        if self._current_tooltip == "initial":
            self._handle_left()
        else:
            self._default_handle('h')

    def _handle_j(self):
        """Key handler, moves cursor down"""
        if self._current_tooltip == "initial":
            self._handle_down()
        else:
            self._default_handle('j')

    def _handle_k(self):
        """Key handler, moves cursor up"""
        if self._current_tooltip == "initial":
            self._handle_up()
        else:
            self._default_handle('k')

    def _handle_l(self):
        """Key handler, moves cursor right"""
        if self._current_tooltip == "initial":
            self._handle_right()
        else:
            self._default_handle('l')

    def _handle_n(self):
        """Key handler, 'no' answer to confirmation prompt"""
        if self._current_tooltip == "initial":
            self.set_tooltip("label_prompt")
        elif self._current_tooltip == "delete":
            self._go_back()
        else:
            self._default_handle('n')

    def _handle_q(self):
        """Key handler, 'quit'"""
        if (self._current_tooltip == "delete"
                or self._current_tooltip == "initial"
                or self._current_tooltip in self.ID_WARNINGS):
            self._go_back()
        else:
            self._default_handle('q')

    def _handle_q_mark(self):
        """Key handler, show help screen"""
        if self._current_tooltip == "initial":
            self._context.change_state("help")
        else:
            self._default_handle('?')

    def _handle_c(self):
        """Key handler, signal intent to give sensor a new label"""
        if self._current_tooltip == "initial":
            self.set_tooltip("rename_prompt")
        else:
            self._default_handle('c')

    def _handle_space(self):
        """Key handler when labelling or renaming sensor"""
        if self._current_tooltip == "label_prompt":
            self._label_input.append(' ')
            self.set_tooltip("label_prompt")
        elif self._current_tooltip == "rename_prompt":
            self._rename_input.append(' ')
            self.set_tooltip("rename_prompt")
        elif self._current_tooltip in self.ID_WARNINGS:
            self._go_back()

    def _handle_y(self):
        """Key handler, 'yes' answer to confirmation prompt"""
        if self._current_tooltip == "delete":
            self._confirm_delete()
        else:
            self._default_handle('y')

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

    def on_mount(self):
        """Change panel border color upon switching to edit mode"""
        self._context.sensors.set_color(self._cursor_color)

    @staticmethod
    def _render_blank_id_tooltip() -> RenderableType:
        """Warning when trying to create sensor with no ID"""
        return Align.center(Text("Sensor ID cannot be blank!",
                                 style=f"bold {Colors.RED.value}",
                                 justify="center"),
                            vertical="middle")

    @staticmethod
    def _render_delete_tooltip() -> RenderableType:
        """Confirmation prompt before deleting sensor"""
        prompt = Align.left(
                    Text("Are you sure? (y/n)",
                         justify="center",
                         style=f"bold {Colors.GREEN.value}"),
                    vertical="middle")
        return prompt

    @staticmethod
    def _render_duplicate_id_tooltip() -> RenderableType:
        """Warning when trying to create sensor without unique ID"""
        return Align.center(Text("Sensor ID already in use!",
                                 style="bold red",
                                 justify="center"),
                            vertical="middle")

    def _render_id_prompt_tooltip(self) -> RenderableType:
        """Input prompt for ID when adding new sensor"""
        prompt = Align.left(
                    Text(f"Sensor ID: {self._id_input.get()}",
                         style=f"bold {Colors.GREEN.value}"),
                    vertical="middle"
                 )
        return prompt

    @staticmethod
    def _render_initial_tooltip() -> RenderableType:
        """Creates Rich Table with key hints for current mode"""
        hint = Table(
            box=None,
            title="EDIT MODE",
            show_header=True,
            show_edge=False,
            title_style=f"bold {Colors.RED.value}",
        )
        hint.add_column()
        hint.add_row("(n)ew     (r)emove   (c)hange label")
        hint.add_row("(?)help   (Enter|q)uit edit mode")
        return Align.center(hint, vertical="middle")

    def _render_label_prompt_tooltip(self) -> RenderableType:
        """Input prompt for label when adding new sensor"""
        prompt = Align.left(
            Text(f"Label for sensor: {self._label_input.get()}",
                 style=f"bold {Colors.GREEN.value}"),
            vertical="middle"
        )
        return prompt

    def _render_rename_prompt_tooltip(self) -> RenderableType:
        """Input prompt for label when renaming sensor"""
        prompt = Align.left(
            Text(f"New label: {self._rename_input.get()}",
                 style=f"bold {Colors.GREEN.value}"),
            vertical="middle"
        )
        return prompt

    def _submit_create(self):
        """Creates new sensor with stored input"""
        id_input = self._id_input.get()
        unique_id = self._context.sensors.is_unique_id(id_input)
        if id_input == "":
            self.set_tooltip("blank_id")
        elif not unique_id:
            self.set_tooltip("duplicate_id")
        else:
            sensors = self._context.sensors
            sensor_id = self._id_input.get().strip()
            sensor_label = self._label_input.get().strip()
            if sensor_label == "":
                sensors.add_sensor(sensor_id)
            else:
                sensors.add_sensor(sensor_id, sensor_label)
            self._go_back()

    def _submit_rename(self):
        """Renames selected sensor with stored input"""
        sensors = self._context.sensors
        new_sensor_label = self._rename_input.get().strip()
        sensors.rename_sensor(new_sensor_label)
        self._go_back()
