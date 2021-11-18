import time
from typing import NamedTuple

import requests
from requests.exceptions import RequestException
from rich import box
from rich.align import Align
from rich.padding import Padding
from rich.status import Status
from rich.table import Table
from rich.text import Text

from config import Colors, Intervals, Layouts, LocationInfo, Units
from plot import Plot
from state import State
import utils


class DetailState(State):
    def __init__(self, context):
        super().__init__(context)
        self._key_handlers = {
            27: self._handle_esc,
            63: self._handle_q_mark,
            'd': self._handle_d,
            'h': self._handle_h,
            'm': self._handle_m,
            'q': self._handle_q,
            'r': self._handle_r,
            'u': self._handle_u,
        }
        self._interval = Intervals.HOUR.value
        self._location_info = None
        self._plot_data = {}
        self._sensor_info = None

    def _build_location_info_table(self, info):
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

    def _build_sensor_info_table(self, info):
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
    def _create_humidity_plot(data_x, data_y, labels=None):
        plot = Plot(data_x, data_y)
        plot.set_title("Humidity")
        plot.set_labels(labels)
        plot.set_legend("% RH")
        plot.set_color("blue")
        return plot

    def _create_temperature_plot(self, data_x, data_y, labels=None):
        temperature_data = (data_y if self._context.unit == Units.C.value
                            else (list(map(utils.c_to_f, data_y))))
        with open('log.txt', 'a') as file:
            file.write('\n' + str(temperature_data))
        plot = Plot(data_x, temperature_data)
        plot.set_title("Temperature")
        plot.set_labels(labels)
        plot.set_legend(f"° {self._context.unit}")
        plot.set_color("red")
        return plot

    def _default_handle(self, key):
        pass

    def _format_location_info(self, info):
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
    def _get_location_info(zip_code):
        endpoint = f"http://localhost:57239/?zip={zip_code}"
        data = None
        try:
            response = requests.get(endpoint)
            data = response.json()
        except RequestException:
            pass
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
        intervals = [Intervals.DAY.value, Intervals.HOUR.value, Intervals.MINUTE.value]
        self._sensor_info = self._context.sensors.update_info()
        self._location_info = self._refresh_location_info(self._sensor_info.location_id)
        self._plot_data = self._context.sensors.update_timeline(intervals)

    def _go_back(self):
        self._clear_details()
        layouts = self._context.layouts
        layouts.get(Layouts.DETAIL.value).visible = False
        layouts.get(Layouts.DASH.value).visible = True
        self._context.change_state("normal")

    def _clear_details(self):
        layouts = self._context.layouts
        layouts.get(Layouts.TEMPERATURE_TIMELINE.value).update("")
        layouts.get(Layouts.HUMIDITY_TIMELINE.value).update("")
        layouts.get(Layouts.SENSOR_INFO.value).update("")
        layouts.get(Layouts.LOCATION_INFO.value).update("")

    def _handle_d(self):
        self._interval = Intervals.DAY.value
        self._render_details()

    def _handle_h(self):
        self._interval = Intervals.HOUR.value
        self._render_details()

    def _handle_m(self):
        self._interval = Intervals.MINUTE.value
        self._render_details()

    def _handle_q_mark(self):
        if self._current_tooltip == "initial":
            layouts = self._context.layouts
            layouts.get(Layouts.DETAIL.value).visible = False
            layouts.get(Layouts.HELP.value).visible = True
            self._context.change_state("help")
        else:
            self._default_handle('?')

    def _handle_r(self):
        self._refresh_details()

    def _handle_u(self):
        self._context.toggle_units()
        self._render_details()

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, value):
        self._interval = value

    def on_mount(self):
        if self._previous_state == "normal":
            self._clear_details()
            self._refresh_details()

    def _render_details(self):
        self._render_sensor_info()
        self._render_location_info()
        self._render_temperature_timeline()
        self._render_humidity_timeline()

    def _render_humidity_timeline(self):
        data_x, data_y, labels = self._plot_data[self._interval]["humidities"]
        layout = self._context.layouts.get(Layouts.HUMIDITY_TIMELINE.value)
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

    def _render_location_info(self):
        layout = self._context.layouts.get(Layouts.LOCATION_INFO.value)
        info = self._location_info
        if info:
            table = self._build_location_info_table(info)
            layout.update(Align.center(table, vertical="middle"))
        else:
            layout.update(Align.center("No location data", vertical="middle"))

    def _render_sensor_info(self):
        layout = self._context.layouts.get(Layouts.SENSOR_INFO.value)
        info = self._sensor_info
        table = self._build_sensor_info_table(info)
        layout.update(Align.center(table, vertical="middle"))

    def _render_temperature_timeline(self):
        data_x, data_y, labels = self._plot_data[self._interval]["temperatures"]
        layout = self._context.layouts.get(Layouts.TEMPERATURE_TIMELINE.value)
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

    @staticmethod
    def render_initial_tooltip():
        hint = Table(
            box=None,
            title="TIMELINE MODE",
            show_header=True,
            show_edge=False,
            title_style=f"bold {Colors.PINK.value}",
        )
        hint.add_column()
        hint.add_column()
        hint.add_column()
        hint.add_row("(m)inutely", "(h)ourly", "(d)aily")
        hint.add_row("(q)uit timeline mode", "(r)efresh", "(u)nit toggle")
        return Align.center(hint, vertical="middle")

    def _refresh_details(self):
        layouts = self._context.layouts
        status = Status(status="",
                        spinner="bouncingBall",
                        spinner_style="bold dark_goldenrod")
        layouts.get(Layouts.SPINNER.value).update(
            Align.center(status, vertical="middle")
        )
        self._get_new_data()
        layouts.get(Layouts.SPINNER.value).visible = False
        layouts.get(Layouts.DETAIL.value).visible = True
        self._render_details()

    def _refresh_location_info(self, location_id):
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
