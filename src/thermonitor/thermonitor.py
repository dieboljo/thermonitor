import argparse
from threading import Event, Thread
import time

from rich.align import Align
from rich.layout import Layout
from rich.live import Live
from rich.padding import Padding

from config import Layouts
from context import Context
from figlettext import FigletText
from keylistener import KeyListener
from sensors import Sensors

def main():
    stop_event = Event()
    try:
        run(stop_event)
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()

def run(stop_event):
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", '-f', help="file location for program state", \
                        default="~/.thermonitor.conf")
    args = parser.parse_args()

    layout = Layout()

    # build layout
    layout.split(Layout(name=Layouts.HEADER.value, ratio=1, minimum_size=4),
                 Layout(name=Layouts.MAIN.value, ratio=6))
    layout["header"].split_row(Layout(name=Layouts.TITLE.value, ratio=3),
                               Layout(name=Layouts.TOOLTIP.value, ratio=2))
    layout["main"].split_column(Layout(name=Layouts.DASH.value, ratio=1),
                                Layout(name=Layouts.DETAIL.value, ratio=1),
                                Layout(name=Layouts.HELP.value, ratio=1),
                                Layout(name=Layouts.SPINNER.value, ratio=1))
    layout["detail"].visible = False
    layout["help"].visible = False
    layout["spinner"].visible = False
    layout["detail"].split_row(Layout(name=Layouts.INFO.value, ratio=1),
                               Layout(name=Layouts.TIMELINE.value, ratio=1))
    layout["info"].split_column(Layout(name=Layouts.SENSOR_INFO.value, ratio=1),
                                Layout(name=Layouts.LOCATION_INFO.value, ratio=1))
    layout["timeline"].split_column(Layout(name=Layouts.TEMPERATURE_TIMELINE.value,
                                       ratio=1),
                                    Layout(name=Layouts.HUMIDITY_TIMELINE.value,
                                       ratio=1))

    # establish context
    context = Context(args.file)
    context.set_layouts(layout)
    sensors = Sensors(context, stop_event)
    context.set_sensors(sensors)

    # load frame
    context.change_state("normal")
    context.load_state()

    # populate layout
    layout["title"].update(
        Padding(Align.center(FigletText("Thermonitor"), vertical="middle"),
                (0, 1)))
    #layout["dash"].update(Align.center(sensors.get_grid()))
    layout["dash"].update(Align.center(sensors))

    # start task to update sensor data
    sensor_task = Thread(target=sensors.run, daemon=True)
    sensor_task.start()

    # start key listener
    listener = KeyListener(context.on_key,
                           stop_event,
                           sensors.get_lock())
    listener_task = Thread(target=listener.listen, daemon=True)
    listener_task.start()

    # start live display
    #with Live(layout, refresh_per_second=20, transient=True):
    with Live(layout, refresh_per_second=20):
        while True:
            listener.handle_char()
            time.sleep(.05)


if __name__ == "__main__":
    main()
