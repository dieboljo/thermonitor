import json
import os

from config import Intervals, Units
from detail import DetailState
from edit import EditState
from help import HelpState
from move import MoveState
from normal import NormalState
import utils

INTERVALS = [Intervals.HOUR.value, Intervals.DAY.value, Intervals.MINUTE.value]
UNITS = [Units.F.value, Units.C.value]

class Context:
    _layouts = None
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

    @property
    def file(self):
        return self._file

    def get_layouts(self):
        return self._layouts

    def get_sensors(self):
        return self._sensors

    def get_state(self):
        return self._state

    def get_unit(self):
        return self._unit

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
            if "unit" in state and state["unit"] in UNITS:
                self._unit = state["unit"]
            if "interval" in state and state["interval"] in INTERVALS:
                self._states["detail"].interval = state["interval"]
            if "sensors" in state:
                for sensor_id, sensor_label in state["sensors"].items():
                    clean_id = utils.sanitize_id(sensor_id)
                    clean_label = utils.sanitize_label(sensor_label)
                    if len(clean_id) > 0:
                        self._sensors.add_sensor(clean_id, clean_label)

    def on_key(self, key):
        self._states[self._state].handle_key(key)

    def save_state(self):
        with open(
            os.path.expanduser(self._file),
            'w'
        ) as outfile:
            state = dict()
            state["sensors"] = self._sensors.sensors
            state["unit"] = self._unit
            state["interval"] = self._states["detail"].interval
            json.dump(state, outfile)

    def set_layouts(self, layouts):
        self._layouts = layouts

    def set_sensors(self, sensors):
        self._sensors = sensors

    def set_unit(self, unit):
        self._unit = unit
