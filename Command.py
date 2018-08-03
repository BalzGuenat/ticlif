from enum import unique, Enum, auto


@unique
class Command(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    BACK = auto()
    NEXT = auto()
    SWITCH = auto()
    OK = auto()
    DELETE = auto()
    DELETE_BEFORE = auto()

    def _generate_next_value_(name, start, count, last_values):
        return name