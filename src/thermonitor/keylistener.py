from queue import Empty, Queue

import nonblocking


class KeyListener:
    def __init__(self, on_press, stop_event, lock=None):
        self._lock = lock
        self._on_press = on_press
        self._queue = Queue()
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
