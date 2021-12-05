"""
Context for the Thermonitor program. Keeps track of the Sensors instance,
Rich layouts, current state, key listener instance, and temperature unit.
"""
from __future__ import annotations
import json
import os
from typing import TYPE_CHECKING, TypedDict

import utils
from config import Intervals, Layouts, States, Units
from detail import DetailState
from edit import EditState
from help import HelpState
from move import MoveState
from normal import NormalState
from sensor import Sensor

if TYPE_CHECKING:
    from keylistener import KeyListener
    from rich.layout import Layout
    from sensors import Sensors
    from state import State

Config = TypedDict('Config',
    { 'unit': str, 'interval': str, 'sensors': list[dict[str, str]] })

INTERVALS = [Intervals.HOUR.value, Intervals.DAY.value, Intervals.MINUTE.value]
UNITS = [Units.F.value, Units.C.value]

class Context:
    """Keeps track of key application instances and state

    Args
    ----
        file: str
            path of config file location (default "~/.thermonitor.conf")
    """

    DASH_STATES = [States.NORMAL.value, States.EDIT.value, States.MOVE.value]

    def __init__(self, file: str):
        self._file = file
        self._interval: str = Intervals.HOUR.value
        self._layouts: Layout = None
        self._listener: KeyListener = None
        self._previous_state = ''
        self._sensors: Sensors = None
        self._state: str = States.NORMAL.value
        self._states: dict[str, State] = {
            States.NORMAL.value: NormalState(self),
            States.EDIT.value: EditState(self),
            States.MOVE.value: MoveState(self),
            States.HELP.value: HelpState(self),
            States.DETAIL.value: DetailState(self),
        }
        self._unit: str = Units.C.value

    def _apply_config(self, config: Config):
        """Applies the loaded config"""
        if "unit" in config and config["unit"] in UNITS:
            self._unit = config["unit"]
        if "interval" in config and config["interval"] in INTERVALS:
            self._interval = config["interval"]
        if "sensors" in config:
            for sensor in config["sensors"]:
                clean_id = utils.sanitize_id(sensor["id"])
                clean_label = utils.sanitize_label(sensor["label"])
                if len(clean_id) > 0:
                    self._sensors.add_sensor(clean_id, clean_label)

    def _change_layout(self):
        next_layout = (Layouts.DASH.value if self._state in self.DASH_STATES
                       else self._state)
        previous_layout = (Layouts.DASH.value if self._previous_state in self.DASH_STATES
                           else self._previous_state)
        if next_layout == previous_layout:
            pass
        else:
            self._layouts.get(previous_layout).visible = False
            self._layouts.get(next_layout).visible = True

    def change_state(self, state_name: str):
        state = self._states[state_name]
        self._previous_state = self._state
        self._state = state_name
        self._change_layout()
        state.set_tooltip("initial")
        state.on_mount()

    def _get_sensor_list(self) -> list[dict[str, str]]:
        """Gets a list of sensor IDs and labels, sorted by grid position"""
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
    def file(self) -> str:
        """Location of config file"""
        return self._file

    @property
    def interval(self) -> str:
        """Current plot interval"""
        return self._interval

    @interval.setter
    def interval(self, value: str):
        """Sets the current plot interval"""
        self._interval = value

    @property
    def layout(self) -> Layout:
        """Rich Layout instance"""
        return self._layouts

    @layout.setter
    def layout(self, value: Layout):
        """Sets the Rich Layout instance"""
        self._layouts = value

    @property
    def listener(self) -> KeyListener:
        """Non-blocking KeyListener instance"""
        return self._listener

    @listener.setter
    def listener(self, value: KeyListener):
        """Sets the KeyListener instance"""
        self._listener = value

    def load_config(self):
        """Loads the configuration from a file into a Dict"""
        file = os.path.expanduser(self._file)
        config = None
        if os.path.exists(file):
            with open(file, 'r') as infile:
                try:
                    config = json.load(infile)
                except ValueError:
                    pass
        if config:
            self._apply_config(config)

    def on_key(self, key: str):
        """Passes a key event to the current state for handling"""
        self._states[self._state].handle_key(key)

    @property
    def previous_state(self) -> str:
        """Gets the name of the previous state"""
        return self._previous_state

    @previous_state.setter
    def previous_state(self, state: str):
        """Sets the name of the previous state, for reference"""
        self._previous_state = state

    def save_config(self):
        """Creates a Dict with the current
        configuration, then writes it to a file
        """
        with open(
            os.path.expanduser(self._file),
            'w'
        ) as outfile:
            unit = self._unit
            interval = self._interval
            sensors = self._get_sensor_list()
            config = Config(unit=unit, interval=interval, sensors=sensors)
            json.dump(config, outfile)

    @property
    def sensors(self) -> Sensors:
        """Sensors instance, a collection of Sensor instances"""
        return self._sensors

    @sensors.setter
    def sensors(self, value: Sensors):
        """Sets the Sensors instance"""
        self._sensors = value

    @property
    def state(self) -> str:
        """The name of the current state"""
        return self._state

    def toggle_units(self):
        """Toggles between 'C' and 'F'"""
        current_unit = self.unit
        new_unit = (Units.F.value
                    if current_unit == Units.C.value
                    else Units.C.value)
        self.unit = new_unit
        self.sensors.set_unit(new_unit)

    @property
    def unit(self) -> str:
        """Current temperature unit, one of 'C' or 'F'"""
        return self._unit

    @unit.setter
    def unit(self, value):
        """Sets the current temperature unit"""
        self._unit = value
