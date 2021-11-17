#import random  # TESTING
from threading import Thread
import time
from typing import NamedTuple

import requests
from rich.console import Console, ConsoleOptions, RenderResult
from rich.padding import Padding
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.table import Column, Table
from rich.text import Text

from config import SensorInfo, Units
import utils

DASH_STATES = ["normal", "edit", "move"]
HOSTNAME = "bko7deq544.execute-api.us-east-2.amazonaws.com/dev"
AUTHORIZATION_TOKEN = "allow"
MAX_WIDTH = 50
MAX_HEIGHT = 9
MIN_HEIGHT = 8

class Sensor:
    """Widget that shows progress bars for temperature and humidity"""
    def __init__(self, sensor_id, unit, label="Sensor"):
        self._sensor_id = sensor_id
        self._label = label
        self._humidity = self.init_humidity()
        self._progress_table = None
        self._temperature = self.init_temperature(unit)
        self._dimensions = PanelDimensions(None, None)

        self.panel = self.init_panel()

    def __rich_console__(self,
                         console: Console,
                         options: ConsoleOptions) -> RenderResult:
        del console, options
        height = (min(self._dimensions.height, MAX_HEIGHT)
                             if self._dimensions.height else None)
        self.panel.height = (max(height, MIN_HEIGHT))
        self.panel.width = (min(self._dimensions.width, MAX_WIDTH)
                            if self._dimensions.width else None)
        yield self.panel

    @staticmethod
    def _calculate_plot_domain(interval):
        end_time = time.time()
        start_time = end_time - (24 * 60 * 60)
        if interval == "minute":
            start_time = end_time - (60 * 60)
        elif interval == "day":
            start_time = end_time - (30 * 24 * 60 * 60)
        return (start_time, end_time)

    @property
    def dimensions(self):
        return self._dimensions

    @dimensions.setter
    def dimensions(self, panel_dimensions):
        self._dimensions = panel_dimensions

    def _fetch_plot_data(self, start_time, end_time):
        endpoint = (f"https://{HOSTNAME}/sensors/devices/{self._sensor_id}"
                    f"?start={start_time}&end={end_time}")
        headers = {'authorization-token': AUTHORIZATION_TOKEN}
        response = requests.get(endpoint, headers=headers)
        data = response.json()
        return data

    def get_sensor_id(self):
        return self._sensor_id

    def get_label(self):
        return self._label

    def get_plot_data(self, interval="hour"):
        start_time, end_time = self._calculate_plot_domain(interval)
        data = self._fetch_plot_data(start_time, end_time)
        if data:
            temperatures = []
            humidities = []
            for entry in data:
                self._parse_data_field(entry, 'Temperature', temperatures)
                self._parse_data_field(entry, 'Humidity', humidities)
            return (temperatures, humidities)
        return ([], [])

    def get_sensor_info(self):
        endpoint = f"https://{HOSTNAME}/sensors/devices/{self._sensor_id}?count=1"
        headers = {'authorization-token': AUTHORIZATION_TOKEN}
        response = requests.get(endpoint, headers=headers)
        data = response.json()
        if data:
            recent = data.pop()
            location = recent['LocationId']['Value'] if 'LocationId' in recent else None
            epoch = float(recent['EpochTime']['Value'])
            temperature = (float(recent['Temperature']['Value'])
                           if 'Temperature' in recent else None)
            humidity = (float(recent['Humidity']['Value'])
                           if 'Humidity' in recent else None)
            return SensorInfo(epoch, self._sensor_id, humidity,
                              self._label, location, temperature)
        return SensorInfo(None, self._sensor_id, None, self._label, None, None)

    @staticmethod
    def init_humidity():
        humidity = Progress("{task.description}", BarColumn(),
                            TextColumn("{task.completed}", table_column=Column(width=5),
                                       justify="right"),
                            " %", expand=True)
        humidity.add_task("[blue]Humidity   ", total=100)
        return humidity

    def init_panel(self):
        self._progress_table = Table.grid()
        self._progress_table.add_row(self._temperature)
        self._progress_table.add_row("")
        self._progress_table.add_row(self._humidity)
        self._progress_table.add_row(
            Padding(
                Text(self._label, style="green", justify="center"),
                (1, 0),
            )
        )
        return Panel(self._progress_table,
                     expand=None,
                     title=f"{self._sensor_id}",
                     padding=(1, 2))

    @staticmethod
    def init_temperature(unit):
        temperature = Progress("{task.description}",
                               BarColumn(),
                               TextColumn("{task.completed}",
                                          table_column=Column(width=5),
                                          justify="right"),
                               TextColumn("°{task.fields[unit]}"),
                               expand=True)
        temperature.add_task("[red]Temperature", total=120, unit=unit)
        return temperature

    @staticmethod
    def _parse_data_field(entry, field_name, value_list):
        if field_name in entry:
            point = (float(entry['EpochTime']['Value']),
                     float(entry[field_name]['Value']))
            value_list.append(point)

    def set_label(self, label):
        self._label = label
        self._progress_table.columns[0]._cells[2] = Padding(
            Text(self._label, style="green", justify="center"),
            (1, 0),
        )

    def set_unit(self, unit):
        task = self._temperature.tasks[0]
        completed = task.completed
        total = task.total
        if unit == 'F':
            completed = utils.c_to_f(completed)
            total = utils.c_to_f(total)
        elif unit == 'C':
            completed = utils.f_to_c(completed)
            total = utils.f_to_c(total)
        self._temperature.update(task.id, completed=completed,
                                 total=total, unit=unit)

    def _update_bars(self, state, unit):
        def closure():
            sensor_info = self.get_sensor_info()
            if sensor_info:
                if sensor_info.humidity:
                    self.update_humidity_bar(sensor_info.humidity, state)
                if sensor_info.temperature:
                    self.update_temperature_bar(sensor_info.temperature, state, unit)
        return closure

    # TESTING
    #def _update_bars(self):
    #    self.update_humidity_bar(random.randrange(0, 101, 1))
    #    self.update_temperature_bar(random.randrange(0, 121, 1))

    def update_panel(self, state, unit, threads=None):
        if threads is not None:
            thread = Thread(target=self._update_bars(state, unit))
            threads.append(thread)
            thread.start()
        else:
            self._update_bars(state, unit)()

    def update_humidity_bar(self, humidity, state):
        task = self._humidity.tasks[0]
        current = task.completed
        delta = humidity - current
        if state in DASH_STATES:
            self._humidity.advance(task.id, delta)

    def update_temperature_bar(self, temperature, state, unit):
        task = self._temperature.tasks[0]
        current = task.completed
        temp = temperature
        if unit != 'C':
            temp = utils.c_to_f(temperature)
        delta = temp - current
        if state in DASH_STATES:
            self._temperature.update(task.id, advance=delta)


class PanelDimensions(NamedTuple):
    height: int
    width: int
