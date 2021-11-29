"""
Sensors holds a group of Sensor objects, and wraps them in rich
renderables to be displayed on the Thermonitor dashboard and referenced
by the rest of the application.
"""
from __future__ import annotations
from threading import Event, Lock
import time
from typing import TYPE_CHECKING

from rich.console import Console, ConsoleOptions, RenderableType, RenderResult
from rich.table import Table

from config import Colors, SensorInfo
import utils
from sensor import PanelDimensions, Sensor

if TYPE_CHECKING:
    from context import Context
    from utils import PlotData

class Sensors:
    """Object that groups other Sensor objects

    Args
    ----
        context: thermonitor.Context
            the context instance for the application
        stop_event: threading.Event
            the signal to be sent to stop waiting threads
    """

    WIDTH = 3

    def __init__(self, context: Context, stop_event: Event):
        self._color: str = Colors.PURPLE.value
        self._context = context
        self._lock = Lock()
        self._stop_event = stop_event
        self._cursor_position = (0, 0)
        self._grid: RenderableType = self._init_grid()

    def __rich_console__(self,
                         console: Console,
                         options: ConsoleOptions) -> RenderResult:
        """Describes how rich Console should render object"""
        del console  # unused parameter
        panel_height = options.max_height / self._grid.row_count
        panel_width = options.max_width / len(self._grid.columns)
        for column in self._grid.columns:
            for cell in list(column.cells):
                if isinstance(cell, Sensor):
                    cell.dimensions = PanelDimensions(int(panel_height), int(panel_width))
        yield self._grid

    def _init_grid(self) -> RenderableType:
        """Creates the grid to house Sensor objects"""
        grid = Table(
            box=None,
            show_edge=False
        )
        for _ in range(self.WIDTH):
            grid.add_column()
        grid.add_row()
        return grid

    def add_sensor(self, sensor_id: str, label="Sensor"):
        """Creates a Sensor object and adds it to grid"""
        first_sensor = self._is_first_sensor()
        sensor = Sensor(sensor_id, self._get_unit(), label)
        if first_sensor:
            sensor.panel.border_style = self._color
        for x, column in enumerate(self._grid.columns):
            cells = list(column.cells)
            for y, cell in enumerate(cells):
                if cell == "":
                    self._set_cell(sensor, x, y)
                    return
        self._grid.add_row(sensor)

    def _get_cell(self, x: int, y: int) -> Sensor:
        """Gets the Sensor instance at coordinates"""
        return self._grid.columns[x]._cells[y]

    def get_grid(self) -> RenderableType:
        """Gets the underlying grid"""
        return self._grid

    def get_lock(self) -> Lock:
        """Gets the associated concurrency lock"""
        return self._lock

    def _get_selected(self) -> Sensor:
        """Gets the Sensor at the current cursor position"""
        selected = self._get_cell(self._cursor_position[0], self._cursor_position[1])
        return selected

    def _get_unit(self) -> str:
        """Gets the current temperature unit"""
        return self._context.unit

    def _get_new_position(self, delta_x: int, delta_y: int) -> tuple[int, int]|None:
        """Gets the new coordinates given a vector"""
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

    def _is_first_sensor(self) -> bool:
        """Checks if there are currently any existing Sensor instances in grid"""
        for column in self._grid.columns:
            for cell in column.cells:
                if isinstance(cell, Sensor):
                    return False
        return True

    def is_unique_id(self, sensor_id: str) -> bool:
        """Checks if the provided ID is in use"""
        for column in self._grid.columns:
            for cell in column.cells:
                if isinstance(cell, Sensor):
                    if cell.get_sensor_id() == sensor_id:
                        return False
        return True

    def move_cursor(self, delta_x: int, delta_y: int):
        """Moves the cursor to new coordinates given a vector"""
        new_position = self._get_new_position(delta_x, delta_y)
        if new_position is not None:
            new_x, new_y = new_position
            cell = self._get_selected()
            next_cell = self._get_cell(new_x, new_y)
            cell.panel.border_style = "none"
            next_cell.panel.border_style = self._color
            self._cursor_position = (new_x, new_y)

    def move_sensor(self, delta_x: int, delta_y: int):
        """Moves the selected sensor to new coordinates given a vector"""
        new_position = self._get_new_position(delta_x, delta_y)
        if new_position is not None:
            new_x, new_y = new_position
            sensor = self._get_selected()
            next_sensor = self._get_cell(new_x, new_y)
            self._set_cell(next_sensor, self._cursor_position[0], self._cursor_position[1])
            self._set_cell(sensor, new_x, new_y)
            self._cursor_position = (new_x, new_y)

    def remove_sensor(self):
        """Removes the selected sensor from the grid"""
        cell = self._get_selected()
        if isinstance(cell, Sensor):
            self._shift_following_cells_down()
            cell = self._get_selected()
            if cell == "":
                self._select_endmost_sensor()
                cell = self._get_selected()
            if isinstance(cell, Sensor):
                cell.panel.border_style = self._color
            self._crop_grid()

    def _crop_grid(self):
        """Removes an empty row from the grid"""
        num_rows = self._grid.row_count
        num_columns = len(self._grid.columns)
        row_empty = True
        for i in range(num_columns):
            if isinstance(self._get_cell(i, num_rows - 1), Sensor):
                row_empty = False
        if row_empty:
            self._grid.rows.pop()
            for column in self._grid.columns:
                column._cells.pop()

    def rename_sensor(self, label: str):
        """Changes the label displayed for the selected sensor"""
        cell = self._get_selected()
        if isinstance(cell, Sensor):
            cell.set_label(label)

    def run(self):
        """Continuously refreshed the dashboard until stop signal occurs"""
        while self._stop_event.is_set() is False:
            with self._lock:
                self._update_dash()
            time.sleep(5)

    def _select_endmost_sensor(self):
        """Moves the cursor to the bottom and far right sensor,
        helpful after removal of more distant sensor
        """
        new_position = self._get_new_position(-1, 0)
        if new_position is not None:
            self._set_selected(new_position[0], new_position[1])
        else:
            new_position = self._get_new_position(0, -1)
            if new_position is not None:
                new_x, new_y = new_position
                self._set_selected(new_x, new_y)
                while self._get_new_position(1, 0):
                    new_x += 1
                    self._set_selected(new_x, new_y)

    def _set_cell(self, sensor: Sensor, x: int, y: int):
        """Sets the provided Sensor instance in grid at coordinates"""
        self._grid.columns[x]._cells[y] = sensor

    def set_color(self, color: str):
        """Changes the panel border color of selected Sensor"""
        selected = self._get_selected()
        self._color = color
        if isinstance(selected, Sensor):
            selected.panel.border_style = self._color

    def _set_selected(self, x: int, y: int):
        """Sets the cursor at provided coordinates"""
        self._cursor_position = (x, y)

    def _shift_following_cells_down(self):
        """Fills the gap in the grid following removal of a cell"""
        x_1, y_1 = self._cursor_position
        x_2 = (x_1 + 1) % self.WIDTH
        y_2 = y_1 if x_2 > 0 else y_1 + 1
        while y_2 < self._grid.row_count:
            next_cell = self._get_cell(x_2, y_2)
            self._set_cell(next_cell, x_1, y_1)
            x_1 = x_2
            y_1 = y_2
            x_2 = (x_1 + 1) % self.WIDTH
            y_2 = y_1 if x_2 > 0 else y_1 + 1
        self._set_cell("", x_1, y_1)

    def set_unit(self, unit: str):
        """Sets the temperature unit ('C' or 'F')"""
        for column in self._grid.columns:
            for cell in column.cells:
                if isinstance(cell, Sensor):
                    cell.set_unit(unit)

    def _update_dash(self):
        """Updates every Sensor in the grid, creating a separate thread for each"""
        threads = []
        for column in self._grid.columns:
            for cell in column.cells:
                if isinstance(cell, Sensor):
                    cell.update_panel(self._context.state, self._get_unit(), threads)
        for thread in threads:
            thread.join()

    def update_info(self) -> SensorInfo:
        """Updates the data for a single sensor"""
        current_sensor = self._get_selected()
        sensor_info = current_sensor.get_sensor_info()
        return sensor_info

    def update_timeline(self, intervals: list[str]) -> dict[str, PlotData]:
        """Updates the plot data for a single sensor"""
        current_sensor = self._get_selected()
        data = dict()
        for interval in intervals:
            temperatures, humidities = current_sensor.get_plot_data(interval)
            temperatures = utils.aggregate(temperatures, interval)
            humidities = utils.aggregate(humidities, interval)
            data[interval] = {"temperatures": temperatures, "humidities": humidities}
        return data
