from typing import *

import logic
import scratch_exceptions


def represents_integer(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False
    