"""
Sensor instantiates a single temperature/humidity sensor that can be
displayed and further accessed from the Thermonitor dashboard.
"""
#import random  # TESTING
from __future__ import annotations
from threading import Thread
import time
from typing import Any, Callable, NamedTuple, Optional, TYPE_CHECKING

import requests
from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderResult, RenderableType
from rich.padding import Padding
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.table import Column, Table
from rich.text import Text

from config import SensorInfo
import utils

if TYPE_CHECKING:
    pass

DataPoint = tuple[float, float]
DataPoints = list[DataPoint]
TelemetryData = dict[str, Any]

class Sensor:
    """Widget that shows progress bars for temperature and humidity

    Args
    ----
        sensor_id: str
            the unique id for the sensor
        unit: str
            the initial temperature unit ['C' | 'F']
        label: str
            the initial label to display for the sensor
    """

    HOSTNAME = "bko7deq544.execute-api.us-east-2.amazonaws.com/dev"
    AUTHORIZATION_TOKEN = "allow"
    MAX_WIDTH = 50
    MAX_HEIGHT = 9
    MIN_HEIGHT = 8

    def __init__(self, sensor_id: str, unit: str, label="Sensor"):
        self._sensor_id = sensor_id
        self._label = label
        self._humidity = self.init_humidity()
        self._progress_table = Table.grid()
        self._temperature: RenderableType = self.init_temperature(unit)
        self._dimensions = PanelDimensions(0, 0)
        self.panel: RenderableType = self.init_panel()

    def __rich_console__(self,
                         console: Console,
                         options: ConsoleOptions) -> RenderResult:
        """Describes how rich Console should render object"""
        del console, options  # unused parameters
        height = (min(self._dimensions.height, self.MAX_HEIGHT)
                             if self._dimensions.height else None)
        self.panel.height = (max(height, self.MIN_HEIGHT)
                             if height else None)
        self.panel.width = (min(self._dimensions.width, self.MAX_WIDTH)
                            if self._dimensions.width else None)
        yield Align.center(self.panel)

    @staticmethod
    def _calculate_plot_domain(interval: str) -> tuple[float, float]:
        """Calculates the time range for desired time division
        ('day', 'hour', or 'minute')"""
        end_time = time.time()
        start_time = end_time - (24 * 60 * 60)
        if interval == "minute":
            start_time = end_time - (60 * 60)
        elif interval == "day":
            start_time = end_time - (3 * 24 * 60 * 60)
        return (start_time, end_time)

    @property
    def dimensions(self) -> PanelDimensions:
        """Property with named tuple of panel's dimensions"""
        return self._dimensions

    @dimensions.setter
    def dimensions(self, panel_dimensions: PanelDimensions):
        """Sets the plot dimensions"""
        self._dimensions = panel_dimensions

    def _fetch_plot_data(self,
                         start_time: float,
                         end_time: float) -> list[TelemetryData]:
        """Retrieves data from external telemetry service"""
        endpoint = (f"https://{self.HOSTNAME}/sensors/devices/{self._sensor_id}"
                    f"?start={start_time}&end={end_time}")
        headers = {'authorization-token': self.AUTHORIZATION_TOKEN}
        response = requests.get(endpoint, headers=headers)
        data: list[TelemetryData] = response.json()
        return data

    def get_sensor_id(self) -> str:
        """Gets the unique identifier of the sensor"""
        return self._sensor_id

    def get_label(self) -> str:
        """Gets the chosen label of the sensor"""
        return self._label

    def get_plot_data(self, interval="hour") -> tuple[DataPoints, DataPoints]:
        """Retrieves sensor data and parses fields to be plotted"""
        start_time, end_time = self._calculate_plot_domain(interval)
        data = self._fetch_plot_data(start_time, end_time)
        if data and isinstance(data, list):
            temperatures: DataPoints = []
            humidities: DataPoints = []
            for entry in data:
                self._parse_data_field(entry, 'Temperature', temperatures)
                self._parse_data_field(entry, 'Humidity', humidities)
            return (temperatures, humidities)
        return ([], [])

    def get_sensor_info(self) -> SensorInfo:
        """Retrives most recent sensor data from external service"""
        endpoint = f"https://{self.HOSTNAME}/sensors/devices/{self._sensor_id}?single=true"
        headers = {'authorization-token': self.AUTHORIZATION_TOKEN}
        response = requests.get(endpoint, headers=headers)
        data = response.json()
        if data and isinstance(data, list):
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
    def init_humidity() -> RenderableType:
        """Creates the humidity meter for the dashboard panel"""
        humidity = Progress("{task.description}", BarColumn(),
                            TextColumn("{task.completed}", table_column=Column(width=5),
                                       justify="right"),
                            " %", expand=True)
        humidity.add_task("[blue]Humidity   ", total=100)
        return humidity

    def init_panel(self) -> RenderableType:
        """Populates the panel for the dashboard grid"""
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
    def init_temperature(unit: str) -> RenderableType:
        """Creates the temperature meter for the dashboard panel"""
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
    def _parse_data_field(entry: TelemetryData,
                          field_name: str,
                          value_list: DataPoints):
        """Gets a point of data from dictionary to display on plot"""
        if field_name in entry:
            point = (float(entry['EpochTime']['Value']),
                     float(entry[field_name]['Value']))
            value_list.append(point)

    def set_label(self, label: str):
        """Sets the label to display for the sensor"""
        self._label = label
        self._progress_table.columns[0]._cells[-1] = Padding(
            Text(self._label, style="green", justify="center"),
            (1, 0),
        )

    def set_unit(self, unit: str):
        """Sets the temperature unit ['C' | 'F']"""
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

    def _update_bars(self, state: str, unit: str) -> Callable[[], None]:
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

    def update_panel(self, state: str, unit: str,
                     threads: Optional[list[Thread]]=None):
        """Updates the temperatures and humidity meters on dashboard panel"""
        if threads is not None:
            thread = Thread(target=self._update_bars(state, unit))
            threads.append(thread)
            thread.start()
        else:
            self._update_bars(state, unit)()

    def update_humidity_bar(self, humidity: float, state: str):
        """Updates the humidity meter on the dashboard panel"""
        task = self._humidity.tasks[0]
        current = task.completed
        delta = humidity - current
        self._humidity.advance(task.id, delta)

    def update_temperature_bar(self, temperature: float,
                               state: str, unit: str):
        """Updates the temperature meter on the dashboard panel"""
        task = self._temperature.tasks[0]
        current = task.completed
        temp = temperature
        if unit != 'C':
            temp = utils.c_to_f(temperature)
        delta = temp - current
        self._temperature.update(task.id, advance=delta)


class PanelDimensions(NamedTuple):
    height: int
    width: int
