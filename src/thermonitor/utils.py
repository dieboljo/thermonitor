from __future__ import annotations
import statistics
import time
from typing import NamedTuple, TYPE_CHECKING

import plotext as plt

if TYPE_CHECKING:
    from sensor import DataPoints

TimeStruct = time.struct_time

VALID_ID_CHARS = "abcdefghijklmnopqrstuvwxyz1234567890"
VALID_LABEL_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'-"

def aggregate(data: DataPoints, interval: str) -> PlotData:
    """Aggregates plot data by chosen time division ['Day' | 'Hour' | 'Minute']"""
    grouped: dict[str, list[float]] = {}
    data_x = []
    data_y = []
    labels_x = []
    for datum in data:
        epoch, point = datum
        time_struct = time.localtime(epoch)
        ftime: str = get_formatted_time(time_struct, interval)
        label = get_label(time_struct, interval)
        rounded = plt.datetime.string_to_timestamp(ftime)
        if rounded in grouped:
            grouped[rounded].append(point)
        else:
            grouped[rounded] = [point]
            labels_x.append(label)
    for key, points in grouped.items():
        data_x.append(key)
        data_y.append(statistics.mean(points))
    return PlotData(data_x, data_y, labels_x)

def get_formatted_time(time_struct: TimeStruct, interval: str) -> str:
    """Rounds time to chosen time division and returns it in a format
    that can be parsed into a timestamp
    """
    year, month, day, hour, minute, *_ = time_struct
    ftime = ""
    if interval == "hour":
        ftime = "{:d}/{:d}/{:d} {:d}:00:00".format(day, month, year, hour)
    elif interval == "minute":
        ftime = "{:d}/{:d}/{:d} {:d}:{:d}:00".format(day, month, year, hour, minute)
    elif interval == "day":
        ftime = "{:d}/{:d}/{:d} 00:00:00".format(day, month, year)
    return ftime

def get_label(time_struct: TimeStruct, interval: str) -> str:
    """Creates a simplified label for chosen time division"""
    _, month, day, hour, minute, *_ = time_struct
    label = ""
    if interval == "hour":
        label = "{:d}:00".format(hour)
    elif interval == "minute":
        label = "{:d}:{:02d}".format(hour, minute)
    elif interval == "day":
        label = "{:d}/{:d}".format(month, day)
    return label

def c_to_f(c: int|float) -> float:
    """Convert temperature value from °C to °F"""
    f = (c * 9 / 5) + 32
    return round(f, 1)

def f_to_c(f: int|float) -> float:
    """Convert temperature value from °F to °C"""
    c = (f - 32) * 5 / 9
    return round(c, 1)

def mps_to_mph(mps: int|float) -> float:
    """Convert meters per second to miles per hour"""
    mph = round(mps * 2.237, 2)
    return mph

def sanitize(dirty: str, valid: str) -> str:
    """Removes invalid characters from string"""
    clean = ''
    for char in dirty:
        if char in valid:
            clean += char
    return clean

def sanitize_label(dirty: str) -> str:
    return sanitize(dirty, VALID_LABEL_CHARS)

def sanitize_id(dirty: str) -> str:
    return sanitize(dirty, VALID_ID_CHARS)


class PlotData(NamedTuple):
    data_x: list[str]
    data_y: list[float]
    labels: list[str]
