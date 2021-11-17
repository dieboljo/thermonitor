import json
import os

from config import Intervals, Units
from detail import DetailState
from edit import EditState
from help import HelpState
from move import MoveState
from normal import NormalState
from sensor import Sensor
import utils

INTERVALS = [Intervals.HOUR.value, Intervals.DAY.value, Intervals.MINUTE.value]
UNITS = [Units.F.value, Units.C.value]

class Context:
    _layouts = None
    _listener = None
    _sensors = None
    _state = None
    _unit = Units.C.value

    def __init__(self, file):
        self._file = file
        self._states = {
            "normal": NormalState(self),
            "edit": EditState(self),
            "move": MoveState(self),
            "help": HelpState(self),
            "detail": DetailState(self),
        }

    def change_state(self, state_name):
        state = self._states[state_name]
        state.set_previous_state(self._state)
        self._state = state_name
        state.set_tooltip("initial")
        state.on_mount()

    def _get_sensor_list(self):
        sensors = []
        columns = self._sensors.get_grid().columns
        cells = [list(column.cells) for column in columns]
        for column in cells:
            column.reverse()
        current_column = 0
        while len(cells[current_column]):
            cell = cells[current_column].pop()
            if isinstance(cell, Sensor):
                sensors.append({"id": cell.get_sensor_id(),
                                "label": cell.get_label()})
            current_column = (current_column + 1) % len(columns)
        return sensors

    @property
    def file(self):
        return self._file

    @property
    def layouts(self):
        return self._layouts

    @layouts.setter
    def layouts(self, value):
        self._layouts = value

    @property
    def listener(self):
        return self._listener

    @listener.setter
    def listener(self, value):
        self._listener = value

    def load_state(self):
        file = os.path.expanduser(self._file)
        state = ""
        if os.path.exists(file):
            with open(file, 'r') as infile:
                try:
                    state = json.load(infile)
                except ValueError:
                    pass
        if state:
            self._set_state(state)

    def on_key(self, key):
        self._states[self._state].handle_key(key)

    def save_state(self):
        with open(
            os.path.expanduser(self._file),
            'w'
        ) as outfile:
            state = dict()
            state["unit"] = self._unit
            state["interval"] = self._states["detail"].interval
            state["sensors"] = self._get_sensor_list()
            json.dump(state, outfile)

    @property
    def sensors(self):
        return self._sensors

    @sensors.setter
    def sensors(self, value):
        self._sensors = value

    def _set_state(self, state):
        if "unit" in state and state["unit"] in UNITS:
            self._unit = state["unit"]
        if "interval" in state and state["interval"] in INTERVALS:
            self._states["detail"].interval = state["interval"]
        if "sensors" in state:
            for sensor in state["sensors"]:
                clean_id = utils.sanitize_id(sensor["id"])
                clean_label = utils.sanitize_label(sensor["label"])
                if len(clean_id) > 0:
                    self._sensors.add_sensor(clean_id, clean_label)

    @property
    def state(self):
        return self._state

    @property
    def unit(self):
        return self._unit

    @unit.setter
    def unit(self, value):
        self._unit = value
