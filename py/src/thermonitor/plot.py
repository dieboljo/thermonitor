"""
Plot creates a bar plot from data provided.
It uses the plotext library to build the graph as ASCII text,
and is renderable and resizable by the rich library.
"""
from __future__ import annotations
from typing import NamedTuple, TYPE_CHECKING

import plotext as plt

if TYPE_CHECKING:
    from rich.console import ConsoleOptions, RenderResult


class Plot:
    """Creates ascii plot renderable for rich

    Args
    ----
        data_x: list[str]
            list of string values for x-axis
        data_y: list[float]
            list of float values for y-axis
    """

    MAX_HEIGHT = 100
    MAX_WIDTH  = 150

    def __init__(self, data_x: list[str], data_y: list[float]):
        self._color = "yellow"
        self._data_x = data_x
        self._data_y = data_y
        self._dimensions = PlotDimensions(0, 0, 0)
        self._labels: list[str]|None = None
        self._legend = ""
        self._title = "Plot"

    def __rich_console__(
        self, _, options: ConsoleOptions
    ) -> RenderResult:
        """Describes how rich Console should render object"""
        self._set_dimensions(options.max_width, options.max_height, padding=2)
        self._configure()
        plot = plt.build()
        plot = plot.replace(self._title, f"[bold dark_goldenrod]{self._title}[/]")
        plot = plot.replace("█", f"[{self._color}]█[/]")

        yield plot

    def _configure(self):
        """Configure plotext options with instance attributes"""
        plt.clp()
        plt.title(self._title)
        plt.plotsize(self._dimensions.width - self._dimensions.padding,
                     self._dimensions.height - self._dimensions.padding)
        plt.scatter(self._data_x, self._data_y, fillx=True,
                    label=self._legend, marker='sd')
        plt.xticks(self._data_x, self._labels)
        plt.xaxis(0, 'upper')
        plt.yaxis(0, 'right')
        plt.colorless()
        plt.ylim(min(self._data_y), max(self._data_y) + 1)

    def get_dimensions(self) -> PlotDimensions:
        """Gets a named tuple with plot dimensions"""
        return self._dimensions

    def get_height(self) -> int:
        """Gets the height of the plot"""
        return self._dimensions.height

    def get_width(self) -> int:
        """Gets the width of the plot"""
        return self._dimensions.width

    def set_color(self, color):
        """Sets the bar colors"""
        self._color = color

    def _set_dimensions(self,
                        console_width: int,
                        console_height: int,
                        padding: int):
        """Creates a named tuple with provided plot dimensions"""
        width = min(console_width, self.MAX_WIDTH)
        height = min(console_height, self.MAX_HEIGHT)
        self._dimensions = PlotDimensions(height, padding, width)

    def set_labels(self, labels: list[str]|None):
        """Sets labels to display for x-axis, otherwise uses data_x values"""
        self._labels = labels

    def set_legend(self, legend: str):
        """Sets the value to display for y-axis values"""
        self._legend = legend

    def set_title(self, title: str):
        """Sets the title of the plot"""
        self._title = title


class PlotDimensions(NamedTuple):
    height: int
    padding: int
    width: int
