from typing import *

import logic
import scratch_exceptions
import pygame


def represents_integer(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False


def color_with_alpha(color, alpha):
    return *color, alpha
