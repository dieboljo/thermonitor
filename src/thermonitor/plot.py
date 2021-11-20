from typing import NamedTuple

import plotext as plt
from rich.console import ConsoleOptions, RenderResult

MAX_HEIGHT = 100
MAX_WIDTH  = 150


class Plot:
    def __init__(self, data_x, data_y):
        self._color = "yellow"
        self._data_x = data_x
        self._data_y = data_y
        self._dimensions = PlotDimensions(0, 0, 0)
        self._labels = None
        self._legend = ""
        self._title = "Plot"

    def __rich_console__(
        self, _, options: ConsoleOptions
    ) -> RenderResult:
        self._set_dimensions(options.max_width, options.max_height, padding=2)
        self._configure()
        plot = plt.build()
        plot = plot.replace(self._title, f"[bold dark_goldenrod]{self._title}[/]")
        plot = plot.replace("█", f"[{self._color}]█[/]")

        yield plot

    def _configure(self):
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

    def get_dimensions(self):
        return self._dimensions

    def get_height(self):
        return self._dimensions.height

    def get_width(self):
        return self._dimensions.width

    def set_color(self, color):
        self._color = color

    def _set_dimensions(self, console_width, console_height, padding):
        width = min(console_width, MAX_WIDTH)
        height = min(console_height, MAX_HEIGHT)
        self._dimensions = PlotDimensions(height, padding, width)

    def set_labels(self, labels):
        self._labels = labels

    def set_legend(self, legend):
        self._legend = legend

    def set_title(self, title):
        self._title = title


class PlotDimensions(NamedTuple):
    height: int
    padding: int
    width: int
