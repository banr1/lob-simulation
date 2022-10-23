from enum import Enum


class Side(Enum):
    LONG = "long"
    SHORT = "short"

    def __init__(self, str_name):
        self.str_name = str_name

    @property
    def opposite(self):
        if self.str_name == "long":
            return Side.SHORT
        elif self.str_name == "short":
            return Side.LONG
        else:
            raise ValueError("invalid value")
