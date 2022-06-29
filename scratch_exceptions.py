from typing import *

import logic


class ScratchRuntimeError(Exception):
    def __init__(self, message):
        self.message = message

    def __repr__(self):
        return self.message


class InvalidVariableName(ScratchRuntimeError):
    def __init__(self, var_name):
        super().__init__(f'Invalid variable {var_name}')


class TypeMismatch(ScratchRuntimeError):
    def __init__(self, expected_type: Type['logic.Value'], actual_type: Type['logic.Value']):
        super().__init__('Type mismatch. Expected: {} Actual: {}'
                         .format(expected_type.get_type_name(), actual_type.get_type_name()))
