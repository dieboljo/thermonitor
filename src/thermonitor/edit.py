from rich.align import Align
from rich.table import Table
from rich.text import Text

from config import Colors, Layouts
from input import Input
from state import State

VALID_ID_CHARS = "abcdefghijklmnopqrstuvwxyz1234567890"
VALID_LABEL_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'-"
ID_WARNINGS = ["blank_id", "duplicate_id"]

class EditState(State):
    def __init__(self, context):
        super().__init__(context)
        self._cursor_color = Colors.RED.value
        self._key_handlers = {
            27: self._handle_esc,
            63: self._handle_q_mark,
            127: self._handle_backspace,
            10: self._handle_enter,
            ' ': self._handle_space,
            'a': self._handle_a,
            'd': self._handle_d,
            'h': self._handle_h,
            'j': self._handle_j,
            'k': self._handle_k,
            'l': self._handle_l,
            'n': self._handle_n,
            'q': self._handle_q,
            'r': self._handle_r,
            'y': self._handle_y,
        }
        self._tooltips = {
            "blank_id": self._render_blank_id_tooltip,
            "delete": self._render_delete_tooltip,
            "duplicate_id": self._render_duplicate_id_tooltip,
            "id_prompt": self._render_id_prompt_tooltip,
            "initial": self._render_initial_tooltip,
            "label_prompt": self._render_label_prompt_tooltip,
            "rename_prompt": self._render_rename_prompt_tooltip,
        }
        self._id_input = Input(VALID_ID_CHARS)
        self._label_input = Input(VALID_LABEL_CHARS)
        self._rename_input = Input(VALID_LABEL_CHARS)

    def _confirm_delete(self):
        self._context.sensors.remove_sensor()
        self._go_back()

    def _default_handle(self, key):
        if self._current_tooltip in ID_WARNINGS:
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
        if self._current_tooltip == "delete":
            self.set_tooltip("initial")
        elif self._current_tooltip == "label_prompt":
            self._label_input.reset()
            self.set_tooltip("initial")
        elif self._current_tooltip == "id_prompt":
            self._label_input.reset()
            self._id_input.reset()
            self.set_tooltip("initial")
        elif self._current_tooltip in ID_WARNINGS:
            self._id_input.reset()
            self.set_tooltip("id_prompt")
        elif self._current_tooltip == "rename_prompt":
            self._rename_input.reset()
            self.set_tooltip("initial")
        else:
            self._context.change_state("normal")

    def _handle_a(self):
        if self._current_tooltip == "initial":
            self.set_tooltip("label_prompt")
        else:
            self._default_handle('a')

    def _handle_backspace(self):
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

    def _handle_d(self):
        if self._current_tooltip == "initial":
            self.set_tooltip("delete")
        else:
            self._default_handle('d')

    def _handle_enter(self):
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
        if self._current_tooltip == "initial":
            self._context.sensors.move_cursor(-1, 0)
        else:
            self._default_handle('h')

    def _handle_j(self):
        if self._current_tooltip == "initial":
            self._context.sensors.move_cursor(0, 1)
        else:
            self._default_handle('j')

    def _handle_k(self):
        if self._current_tooltip == "initial":
            self._context.sensors.move_cursor(0, -1)
        else:
            self._default_handle('k')

    def _handle_l(self):
        if self._current_tooltip == "initial":
            self._context.sensors.move_cursor(1, 0)
        else:
            self._default_handle('l')

    def _handle_n(self):
        if self._current_tooltip == "delete":
            self._go_back()
        else:
            self._default_handle('n')

    def _handle_q(self):
        if (self._current_tooltip == "delete"
                or self._current_tooltip == "initial"
                or self._current_tooltip in ID_WARNINGS):
            self._go_back()
        else:
            self._default_handle('q')

    def _handle_q_mark(self):
        if self._current_tooltip == "initial":
            layouts = self._context.layouts
            layouts.get(Layouts.DASH.value).visible = False
            layouts.get(Layouts.HELP.value).visible = True
            self._context.change_state("help")
        else:
            self._default_handle('?')

    def _handle_r(self):
        if self._current_tooltip == "initial":
            self.set_tooltip("rename_prompt")
        else:
            self._default_handle('r')

    def _handle_space(self):
        if self._current_tooltip == "label_prompt":
            self._label_input.append(' ')
            self.set_tooltip("label_prompt")
        elif self._current_tooltip == "rename_prompt":
            self._rename_input.append(' ')
            self.set_tooltip("rename_prompt")
        elif self._current_tooltip in ID_WARNINGS:
            self._go_back()

    def _handle_y(self):
        if self._current_tooltip == "delete":
            self._confirm_delete()
        else:
            self._default_handle('y')

    def on_mount(self):
        self._context.sensors.set_color(self._cursor_color)

    @staticmethod
    def _render_blank_id_tooltip():
        return Align.center(Text("Sensor ID cannot be blank!",
                                 style="bold red",
                                 justify="center"),
                            vertical="middle")

    @staticmethod
    def _render_delete_tooltip():
        prompt = Align.left(
                    Text("Are you sure? (y/n)",
                         justify="center"),
                    vertical="middle")
        return prompt

    @staticmethod
    def _render_duplicate_id_tooltip():
        return Align.center(Text("Sensor ID already in use!",
                                 style="bold red",
                                 justify="center"),
                            vertical="middle")

    def _render_id_prompt_tooltip(self):
        prompt = Align.left(
                    Text(f"Sensor ID: {self._id_input.get()}"),
                    vertical="middle"
                 )
        return prompt

    @staticmethod
    def _render_initial_tooltip():
        hint = Table(
            box=None,
            title="EDIT MODE",
            show_header=True,
            show_edge=False,
            title_style=f"bold {Colors.RED.value}",
        )
        hint.add_column()
        hint.add_column()
        hint.add_column()
        hint.add_row("(a)dd", "(d)elete", "(Enter|q)uit edit mode")
        hint.add_row("(r)ename", "(?)help")
        return Align.center(hint, vertical="middle")

    def _render_label_prompt_tooltip(self):
        prompt = Align.left(
            Text(f"Label for sensor: {self._label_input.get()}"),
            vertical="middle"
        )
        return prompt

    def _render_rename_prompt_tooltip(self):
        prompt = Align.left(
            Text(f"New label: {self._rename_input.get()}"),
            vertical="middle"
        )
        return prompt

    def _submit_create(self):
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
        sensors = self._context.sensors
        new_sensor_label = self._rename_input.get().strip()
        sensors.rename_sensor(new_sensor_label)
        self._go_back()
