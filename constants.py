import enum

EMPTY_BRICK_SLOT_WIDTH = 50
EMPTY_BRICK_SLOT_HEIGHT = 20

EMPTY_BLOCK_SPOT_WIDTH = 40
EMPTY_BLOCK_SPOT_HEIGHT = 20

LEFT_MOUSE_BUTTON = 1

BACKGROUND_COLOR = (0, 0, 0)


class TriggeredEvent(enum.Enum):
    SPACE_PRESSED_EVENT = 1
