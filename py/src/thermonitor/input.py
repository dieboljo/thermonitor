"""
Input manages values retrieved from input prompts.
"""
from __future__ import annotations

class Input:
    """Manages input data

    Args
    ----
        valid_chars: str
            string sequence of acceptable characters
    """
    def __init__(self, valid_chars: str):
        self._chars = ""
        self._valid_chars = valid_chars

    def append(self, char):
        self._chars += char

    def append_clean(self, char):
        for valid in self._valid_chars:
            if char == valid:
                self.append(char)

    def get(self) -> str:
        return self._chars

    def pop(self):
        self._chars = self._chars[:-1]

    def reset(self):
        self._chars = ""
