import logging

from rich.console import Console
from rich.logging import RichHandler


class Logger:
    def __init__(self, file):
        self._file = file
        self._console = Console()
        self._logger = self._init_logger()

    def _init_logger(self):
        logging.basicConfig(
            level="NOTSET",
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(
                rich_tracebacks=True,
                console=self._console,
            )]
        )
        logger = logging.getLogger("rich")
        return logger

    def debug(self, text):
        with open(self._file, 'a') as log_file:
            self._console.file = log_file
            self._logger.debug(text)

logger = Logger("log.txt")
