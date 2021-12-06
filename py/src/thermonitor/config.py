from enum import Enum
from typing import NamedTuple


class Colors(Enum):
    CYAN = "cyan"
    GREEN = "green"
    GREY = "navajo_white3"
    PINK = "deep_pink4"
    RED = "red"
    PURPLE = "blue3"
    YELLOW = "yellow"

class Intervals(Enum):
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"

class Layouts(Enum):
    CONFIRM = "confirm"
    DASH = "dash"
    DETAIL = "detail"
    HEADER = "header"
    HELP = "help"
    HUMIDITY = "humidity"
    HUMIDITY_TIMELINE = "humidity timeline"
    HUMIDITY_SPINNER = "humidity spinner"
    INFO = "info"
    SENSOR_INFO = "sensor info"
    SPINNER = "spinner"
    LOCATION_INFO = "location info"
    TEMPERATURE = "temperature"
    TEMPERATURE_TIMELINE = "temperature timeline"
    TEMPERATURE_SPINNER = "temperature spinner"
    TIMELINE = "timeline"
    TOOLTIP = "tooltip"
    TOOLTIP_CONTENT = "tooltip content"
    TOOLTIP_SPINNER = "tooltip spinner"
    MAIN = "main"
    TITLE = "title"

class LocationInfo(NamedTuple):
    city: str
    humidity: float
    pressure: str
    temperature: float
    wind_direction: int
    wind_speed: float
    zip_code: int

class SensorInfo(NamedTuple):
    epoch_time: float
    device_id: str
    humidity: float
    label: str
    location_id: str
    temperature: float

class States(Enum):
    DETAIL = "detail"
    EDIT = "edit"
    HELP = "help"
    MOVE = "move"
    NORMAL = "normal"

class Units(Enum):
    F = 'F'
    C = 'C'
