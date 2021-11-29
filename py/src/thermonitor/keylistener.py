"""
KeyListener manages a queue of keypress events,
and processes them in turn with the supplied function.
It must be run on its own thread.
"""
from __future__ import annotations
from queue import Empty, Queue
from typing import Callable, TYPE_CHECKING

import nonblocking

if TYPE_CHECKING:
    from threading import Event, Lock

class KeyListener:
    """Key listener agent

    Args
    ----
        on_press: (str | int)
            key handler function, will be passed a character
            or integer representing the Unicode code of a character
        stop_event: threading.Event
            an event object that sends a signal to other waiting threads
        lock: threading.Lock
            a lock primitive for concurrency control
    """
    def __init__(self,
                 on_press: Callable[[str|int], None],
                 stop_event: Event,
                 lock: Lock=None):
        self._lock = lock
        self._on_press = on_press
        self._queue: Queue = Queue()
        self._stop_event = stop_event

    def handle_char(self):
        try:
            char = self._queue.get_nowait()
        except Empty:
            pass
        else:
            if self._lock:
                with self._lock:
                    self._on_press(char)
            else:
                self._on_press(char)

    def listen(self):
        while self._stop_event.is_set() is False:
            char = nonblocking.read_key()
            if ord(char) == 27:
                self._queue.put(27)
            elif ord(char) == 10:
                self._queue.put(10)
            elif ord(char) == 63:
                self._queue.put(63)
            elif ord(char) == 127:
                self._queue.put(127)
            else:
                self._queue.put(char)
