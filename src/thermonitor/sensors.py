from threading import Lock
import time

from rich.console import Console, ConsoleOptions, RenderResult
from rich.table import Table

from config import Colors, WIDTH
import utils
from sensor import PanelDimensions, Sensor


class Sensors:

    def __init__(self, context, stop_event):
        self._color = Colors.PURPLE.value
        self._context = context
        self._lock = Lock()
        self._sensors = dict()
        self._stop_event = stop_event
        self._cursor_position = (0, 0)
        self._grid = self._init_grid()

    def __rich_console__(self,
                         console: Console,
                         options: ConsoleOptions) -> RenderResult:
        del console
        panel_height = options.max_height / len(self._grid.columns[0]._cells)
        panel_width = options.max_width / len(self._grid.columns)
        for column in self._grid.columns:
            for cell in column._cells:
                if isinstance(cell, Sensor):
                    cell.dimensions = PanelDimensions(int(panel_height), int(panel_width))
        yield self._grid

    def _init_grid(self):
        grid = Table(
            box=None,
            show_edge=False
        )
        for _ in range(WIDTH):
            grid.add_column()
        grid.add_row()
        return grid

    def add_sensor(self, sensor_id, label="Sensor"):
        if sensor_id not in self._sensors:
            sensor = Sensor(sensor_id, self._get_unit(), label)
            if len(self._sensors) == 0:
                sensor.panel.border_style = self._color
            self._sensors[sensor_id] = label
            for column in self._grid.columns:
                for i, cell in enumerate(column._cells):
                    if cell == "":
                        column._cells[i] = sensor
                        return
            self._grid.add_row(sensor)

    def _get_cell(self, x, y):
        return self._grid.columns[x]._cells[y]

    def get_grid(self):
        return self._grid

    def get_lock(self):
        return self._lock

    def _get_selected(self):
        selected = self._get_cell(self._cursor_position[0], self._cursor_position[1])
        return selected

    @property
    def sensors(self):
        return self._sensors

    def _get_unit(self):
        return self._context.get_unit()

    def _get_new_position(self, delta_x, delta_y):
        new_x = self._cursor_position[0] + delta_x
        new_y = self._cursor_position[1] + delta_y
        if (new_x < 0 or new_x >= len(self._grid.columns)
                or new_y < 0 or new_y >= self._grid.row_count):
            return None
        next_cell = self._get_cell(new_x, new_y)
        if next_cell == "":
            return None
        if isinstance(next_cell, Sensor):
            return (new_x, new_y)
        return None

    def move_cursor(self, delta_x, delta_y):
        new_position = self._get_new_position(delta_x, delta_y)
        if new_position is not None:
            new_x, new_y = new_position
            cell = self._get_selected()
            next_cell = self._get_cell(new_x, new_y)
            cell.panel.border_style = "none"
            next_cell.panel.border_style = self._color
            self._cursor_position = (new_x, new_y)

    def move_sensor(self, delta_x, delta_y):
        new_position = self._get_new_position(delta_x, delta_y)
        if new_position is not None:
            new_x, new_y = new_position
            sensor = self._get_selected()
            next_sensor = self._get_cell(new_x, new_y)
            self._set_cell(next_sensor, self._cursor_position[0], self._cursor_position[1])
            self._set_cell(sensor, new_x, new_y)
            self._cursor_position = (new_x, new_y)

    def remove_sensor(self):
        cell = self._get_selected()
        if isinstance(cell, Sensor):
            sensor = cell
            sensor_id = sensor.get_sensor_id()
            x_1 = self._cursor_position[0]
            y_1 = self._cursor_position[1]
            x_2 = (x_1 + 1) % WIDTH
            y_2 = y_1 if x_2 > 0 else y_1 + 1
            while y_2 < self._grid.row_count:
                next_cell = self._get_cell(x_2, y_2)
                self._set_cell(next_cell, x_1, y_1)
                x_1 = x_2
                y_1 = y_2
                x_2 = (x_1 + 1) % WIDTH
                y_2 = y_1 if x_2 > 0 else y_1 + 1
            self._set_cell("", x_1, y_1)
            self._sensors.pop(sensor_id)
            cell = self._get_selected()
            if cell == "":
                new_position = self._get_new_position(-1, 0)
                if new_position is not None:
                    self._set_selected(new_position[0], new_position[1])
                else:
                    new_position = self._get_new_position(0, -1)
                    if new_position is not None:
                        new_x, new_y = new_position
                        while self._get_new_position(1, 0):
                            new_x += 1
                        self._set_selected(new_x, new_y)
                cell = self._get_selected()
            if isinstance(cell, Sensor):
                cell.panel.border_style = self._color

    def rename_sensor(self, label):
        cell = self._get_selected()
        if isinstance(cell, Sensor):
            sensor_id = cell.get_sensor_id()
            cell.set_label(label)
            self._sensors[sensor_id] = label

    def run(self):
        while self._stop_event.is_set() is False:
            with self._lock:
                self._update_dash()
            time.sleep(5)

    def _set_cell(self, renderable, x, y):
        self._grid.columns[x]._cells[y] = renderable

    def set_color(self, color):
        selected = self._get_selected()
        self._color = color
        if isinstance(selected, Sensor):
            selected.panel.border_style = self._color

    def set_context(self, context):
        self._context = context

    def _set_selected(self, x, y):
        self._cursor_position = (x, y)

    def toggle_units(self):
        for column in self._grid.columns:
            for cell in column.cells:
                if isinstance(cell, Sensor):
                    cell.set_unit(self._get_unit())

    def _update_dash(self):
        threads = []
        for column in self._grid.columns:
            for cell in column.cells:
                if isinstance(cell, Sensor):
                    cell.update_panel(self._context.get_state(), self._get_unit(), threads)
        for thread in threads:
            thread.join()

    def update_info(self):
        current_sensor = self._get_selected()
        sensor_info = current_sensor.get_sensor_info()
        return sensor_info

    def update_timeline(self, intervals):
        current_sensor = self._get_selected()
        data = dict()
        for interval in intervals:
            temperatures, humidities = current_sensor.get_plot_data(self._get_unit(), interval)
            temperatures = utils.aggregate(temperatures, interval)
            humidities = utils.aggregate(humidities, interval)
            data[interval] = {"temperatures": temperatures, "humidities": humidities}
        return data
