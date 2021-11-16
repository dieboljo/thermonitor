from rich.console import Console, ConsoleOptions, RenderResult
from rich.text import Text

try:
    from pyfiglet import Figlet
except ImportError:
    print("Please install pyfiglet to run this example")
    raise


class FigletText:
    """A renderable to generate figlet text that adapts to fit the container."""

    def __init__(self, text: str) -> None:
        self.text = text

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Build a Rich renderable to render the Figlet text."""
        width = options.max_width
        height = options.max_height
        size = min(options.max_width / 2, options.max_height)
        if height < 3 or width < 30:
            yield Text(self.text, style="bold")
        else:
            if height < 5 or width < 50:
                font_name = "mini"
            elif height < 6 or width < 65:
                font_name = "small"
            elif height < 7 or width < 70:
                font_name = "standard"
            else:
                font_name = "big"
            font = Figlet(font=font_name, width=options.max_width)
            yield Text(font.renderText(self.text).rstrip("\n"), style="bold")
