"""
DetailState manages the state of Thermonitor's timeline view.
Manages the specific sensor's info, location info, and plots of
both the temperature and the humidity.
"""
from __future__ import annotations
import time
from typing import Callable, NamedTuple, TYPE_CHECKING

import requests
from requests.exceptions import RequestException
from rich import box
from rich.align import Align
from rich.console import RenderableType
from rich.padding import Padding
from rich.status import Status
from rich.table import Table
from rich.text import Text

from config import Colors, Intervals, Layouts, LocationInfo, SensorInfo, Units
from plot import Plot
from state import State
import utils

if TYPE_CHECKING:
    from context import Context
    from utils import PlotData

class DetailState(State):
    """Keeps track of minutely, hourly, and daily data, as well as
    sensor and location info.

    Args
    ----
        context: thermonitor.Context
            the current Context instance of the process
    """
    def __init__(self, context: Context):
        super().__init__(context)
        self._key_handlers: dict[int|str, Callable[[], None]] = {
            27: self._handle_esc,
            63: self._handle_q_mark,
            'd': self._handle_d,
            'h': self._handle_h,
            'm': self._handle_m,
            'q': self._handle_q,
            'r': self._handle_r,
            'u': self._handle_u,
        }
        self._interval: str = Intervals.HOUR.value
        self._location_info: LocationInfo = None
        self._plot_data: dict[str, dict[str, PlotData]] = {}
        self._sensor_info: SensorInfo = None

    def _build_location_info_table(self, info: FormattedLocationInfo) -> Table:
        """Builds a Rich Table with data retrieved from weather service"""
        f_info = self._format_location_info(info)
        table = Table(box=box.HORIZONTALS, expand=True,
                      title=(f_info.city if f_info.city else f_info.zip_code),
                      show_header=False, show_edge=True, title_style="bold dark_goldenrod")
        table.add_column(style="light_coral", justify="right", width=20)
        table.add_column(width=30)
        table.add_row("Temperature: ", f_info.temperature)
        table.add_row("Humidity: ", f_info.humidity)
        table.add_row("Pressure: ", f_info.pressure)
        table.add_row("Wind Direction: ", f_info.wind_direction)
        table.add_row("Wind Speed: ", f_info.wind_speed)
        return table

    def _build_sensor_info_table(self, info: SensorInfo) -> Table:
        """Builds a Rich Table with current sensor info, retrieved telemetry service"""
        table = Table(box=box.HORIZONTALS, expand=True, title=info.label,
                      show_header=False, show_edge=True, title_style="bold dark_goldenrod")
        last_updated = ''
        if info.epoch_time:
            local_time = time.localtime(info.epoch_time)
            last_updated = time.asctime(local_time)
        table.add_column(style="light_coral", justify="right", width=20)
        table.add_column(width=30)
        table.add_row("Sensor ID: ", info.device_id)
        table.add_row("Last updated: ", last_updated)
        temp_unit = self._context.unit
        if info.temperature:
            temperature = (info.temperature if self._context.unit == 'C'
                           else utils.c_to_f(info.temperature))
            table.add_row("Temperature: ", str(temperature) + f" °{temp_unit}")
        if info.humidity:
            table.add_row("Humidity: ", str(info.humidity) + " %")
        return table

    @staticmethod
    def _create_humidity_plot(data_x: list[float], data_y: list[float],
                              labels: list[str]) -> Plot:
        """Creates a Plot instance, using plotext library
        with time and humidity data from telemetry service
        """
        plot = Plot(data_x, data_y)
        plot.set_title("Humidity")
        plot.set_labels(labels)
        plot.set_legend("% RH")
        plot.set_color("blue")
        return plot

    def _create_temperature_plot(self, data_x: list[float],
                                 data_y: list[float], labels: list[str]) -> Plot:
        """Creates a Plot instance, using plotext library
        with time and temperature data from telemetry service
        """
        temperature_data = (data_y if self._context.unit == Units.C.value
                            else (list(map(utils.c_to_f, data_y))))
        plot = Plot(data_x, temperature_data)
        plot.set_title("Temperature")
        plot.set_labels(labels)
        plot.set_legend(f"° {self._context.unit}")
        plot.set_color("red")
        return plot

    def _default_handle(self, key: str):
        pass

    def _format_location_info(self, info: LocationInfo) -> FormattedLocationInfo:
        temp_unit = self._context.unit
        wind_speed_unit = 'm/s'
        temperature = info.temperature
        wind_speed = info.wind_speed
        if temp_unit == Units.F.value:
            wind_speed_unit = 'mph'
            temperature = utils.c_to_f(temperature)
            wind_speed = utils.mps_to_mph(wind_speed)
        return FormattedLocationInfo(info.city, f"{info.humidity} %", f"{info.pressure} hPa",
                                     f"{temperature} °{temp_unit}", f"{info.wind_direction} °",
                                     f"{wind_speed} {wind_speed_unit}", str(info.zip_code))

    @staticmethod
    def _get_location_info(zip_code: str) -> LocationInfo:
        """Retrieves info about sensor's location from weather service"""
        endpoint = f"http://localhost:57239/?zip={zip_code}"
        response = None
        try:
            response = requests.get(endpoint)
        except RequestException:
            pass
        data = response.json() if response else None
        if data:
            city = data["name"]
            humidity = data["main"]["humidity"]
            temperature = data["main"]["temp"]
            pressure = data["main"]["pressure"]
            wind_speed = data["wind"]["speed"]
            wind_direction = data["wind"]["deg"]
            return LocationInfo(city, humidity, pressure, temperature,
                                wind_direction, wind_speed, int(zip_code))
        return None

    def _get_new_data(self):
        """Retrieves latest sensor data, info about sensor's location,
        and sensor data over different time periods"""
        intervals = [Intervals.DAY.value, Intervals.HOUR.value, Intervals.MINUTE.value]
        self._sensor_info = self._context.sensors.update_info()
        self._location_info = self._refresh_location_info(self._sensor_info.location_id)
        self._plot_data = self._context.sensors.update_timeline(intervals)

    def _go_back(self):
        """Goes back to dashboard"""
        self._clear_details()
        layout = self._context.layout
        layout.get(Layouts.DETAIL.value).visible = False
        layout.get(Layouts.DASH.value).visible = True
        self._context.change_state("normal")

    def _clear_details(self):
        """Clears the current sensor's data from the screen"""
        layout = self._context.layout
        layout.get(Layouts.TEMPERATURE_TIMELINE.value).update("")
        layout.get(Layouts.HUMIDITY_TIMELINE.value).update("")
        layout.get(Layouts.SENSOR_INFO.value).update("")
        layout.get(Layouts.LOCATION_INFO.value).update("")

    def _handle_d(self):
        """Key handler, displays plot data aggregated by day"""
        self._interval = Intervals.DAY.value
        self._render_details()

    def _handle_h(self):
        """Key handler, displays plot data aggregated by hour"""
        self._interval = Intervals.HOUR.value
        self._render_details()

    def _handle_m(self):
        """Key handler, displays plot data aggregated by minute"""
        self._interval = Intervals.MINUTE.value
        self._render_details()

    def _handle_q_mark(self):
        """Key handler, shows help screen"""
        if self._current_tooltip == "initial":
            layout = self._context.layout
            layout.get(Layouts.DETAIL.value).visible = False
            layout.get(Layouts.HELP.value).visible = True
            self._context.change_state("help")
        else:
            self._default_handle('?')

    def _handle_r(self):
        """Key handler, refreshes data of currently displayed sensor"""
        self._refresh_details()

    def _handle_u(self):
        """Key handler, toggles temperature units ['C' | 'F']"""
        self._context.toggle_units()
        self._render_details()

    @property
    def interval(self) -> str:
        """Current plot interval, one of 'minute', 'hour', or 'day'"""
        return self._interval

    @interval.setter
    def interval(self, value: str):
        """Sets current plot interval, one of 'minute', 'hour', or 'day'"""
        self._interval = value

    def on_mount(self):
        """Initialize view and refresh data if coming from dashboard,
        skip if coming from help screen"""
        if self._previous_state == "normal":
            self._clear_details()
            self._refresh_details()

    def _render_details(self):
        self._render_sensor_info()
        self._render_location_info()
        self._render_temperature_timeline()
        self._render_humidity_timeline()

    def _render_humidity_timeline(self):
        """Creates humidity plot with current data and currently selected interval"""
        data_x, data_y, labels = self._plot_data[self._interval]["humidities"]
        layout = self._context.layout.get(Layouts.HUMIDITY_TIMELINE.value)
        if data_x and data_y:
            plot = self._create_humidity_plot(data_x, data_y, labels)
            padding = plot.get_dimensions().padding
            layout.update(Padding(Align.center(plot, vertical="middle"), padding))
        else:
            if self._interval == Intervals.MINUTE.value:
                layout.update(Align.center(Text("No minutely humidity data"), vertical="middle"))
            elif self._interval == Intervals.HOUR.value:
                layout.update(Align.center(Text("No hourly humidity data"), vertical="middle"))
            elif self._interval == Intervals.DAY.value:
                layout.update(Align.center(Text("No daily humidity data"), vertical="middle"))

    @staticmethod
    def render_initial_tooltip() -> RenderableType:
        """Creates Rich Table with key hints for current mode"""
        hint = Table(
            box=None,
            title="TIMELINE MODE",
            show_header=True,
            show_edge=False,
            title_style=f"bold {Colors.PINK.value}",
        )
        hint.add_column()
        hint.add_row("(m)inutely  (h)ourly  (d)aily  (u)nit")
        hint.add_row("(r)efresh   (?)help   (q)uit timeline mode")
        return Align.center(hint, vertical="middle")

    def _render_location_info(self):
        """Creates panel with sensor location info"""
        layout = self._context.layout.get(Layouts.LOCATION_INFO.value)
        info = self._location_info
        if info:
            table = self._build_location_info_table(info)
            layout.update(Align.center(table, vertical="middle"))
        else:
            layout.update(Align.center("No location data", vertical="middle"))

    def _render_sensor_info(self):
        """Creates panel with latest sensor data"""
        layout = self._context.layout.get(Layouts.SENSOR_INFO.value)
        info = self._sensor_info
        table = self._build_sensor_info_table(info)
        layout.update(Align.center(table, vertical="middle"))

    def _render_temperature_timeline(self):
        """Creates temperature plot with current data and currently selected interval"""
        data_x, data_y, labels = self._plot_data[self._interval]["temperatures"]
        layout = self._context.layout.get(Layouts.TEMPERATURE_TIMELINE.value)
        if data_x and data_y:
            plot = self._create_temperature_plot(data_x, data_y, labels)
            padding = plot.get_dimensions().padding
            layout.update(Padding(Align.center(plot, vertical="middle"), padding))
        else:
            if self._interval == Intervals.MINUTE.value:
                layout.update(Align.center(Text("No minutely temperature data"), vertical="middle"))
            elif self._interval ==Intervals.HOUR.value:
                layout.update(Align.center(Text("No hourly temperature data"), vertical="middle"))
            elif self._interval ==Intervals.DAY.value:
                layout.update(Align.center(Text("No daily temperature data"), vertical="middle"))

    def _refresh_details(self):
        """Displays spinner while fetching new data"""
        layout = self._context.layout
        status = Status(status="",
                        spinner="bouncingBall",
                        spinner_style="bold dark_goldenrod")
        layout.get(Layouts.SPINNER.value).update(
            Align.center(status, vertical="middle")
        )
        self._get_new_data()
        layout.get(Layouts.SPINNER.value).visible = False
        layout.get(Layouts.DETAIL.value).visible = True
        self._render_details()

    def _refresh_location_info(self, location_id: str) -> LocationInfo|None:
        if location_id:
            location_info = self._get_location_info(location_id)
            return location_info
        return None

class FormattedLocationInfo(NamedTuple):
    city: str
    humidity: str
    pressure: str
    temperature: str
    wind_direction: str
    wind_speed: str
    zip_code: str
