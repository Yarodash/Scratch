from typing import *

import colorsys
import scratch_exceptions
import pygame
import re


def represents_integer(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False


def represents_variable_name(value: str) -> bool:
    return bool(re.match(r'[a-z][a-z0-9]*', value))


def color_with_alpha(color, alpha):
    return *color, alpha


def apply_key(text: str, key: int) -> str:
    if key == pygame.K_BACKSPACE:
        return text[:-1]

    if key == pygame.K_MINUS:
        return text + '-'

    if key in range(pygame.K_a, pygame.K_z + 1):
        return text + chr(key)

    if key in range(pygame.K_0, pygame.K_9 + 1):
        return text + chr(key)

    return text


class ColorGenerator:

    def __init__(self, saturation: float, brightness: float):
        self.first_three_colors: int = 0
        self.step: float = 1 / 3
        self.i: int = 0
        self.max_steps: int = 3

        self.saturation: float = saturation
        self.brightness: float = brightness

    def get_color_from_hue(self, hue: float) -> Tuple[float, float, float]:
        color = colorsys.hsv_to_rgb(hue, self.saturation, self.brightness)
        return color[0] * 255, color[1] * 255, color[2] * 255

    def new_color(self) -> Tuple[float, float, float]:
        if self.first_three_colors < 3:
            color = ([0, 255][self.first_three_colors == 0],
                     [0, 255][self.first_three_colors == 1],
                     [0, 255][self.first_three_colors == 2])
            self.first_three_colors += 1
            return color

        color = self.get_color_from_hue(self.step / 2 + self.step * self.i)
        self.i += 1

        if self.i == self.max_steps:
            self.i, self.max_steps, self.step = 0, self.max_steps * 2, self.step / 2

        return color


color_generator = ColorGenerator(0.8, 1)
