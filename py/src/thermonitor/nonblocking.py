"""
This module puts the terminal into cbreak mode, so that characters
can be read one at a time, and restores the old settings on exit.
It uses different tools for Windows and Unix.
"""
from __future__ import annotations, print_function

try:
    """Windows configuration"""
    import msvcrt

    def key_pressed():
        return msvcrt.kbhit()

    def read_key():
        key = msvcrt.getch()

        try:
            result = str(key, encoding="utf8")
        except:
            result = key

        return result

except:

    try:
        import sys
        import select
        import tty
        import termios
        import atexit

        def key_pressed():
            return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

        def read_key():
            """Waits for and reads one character from stdin"""
            return sys.stdin.read(1)

        def restore_settings():
            """Restores original tty settings"""
            old_settings = termios.tcgetattr(sys.stdin)
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

        atexit.register(restore_settings)

        tty.setcbreak(sys.stdin.fileno())
    except:
        print("Can't deal with your keyboard!")


if __name__ == "__main__":

    print("Press any key")
    while True:
        char = read_key()
        if char == ' ':
            print(f"Space: {ord(char)}")
        else:
            print(f"{char}: {ord(char)}")
