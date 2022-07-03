from typing import *


class ScratchRuntimeException(Exception):
    def __init__(self, message):
        self.message = message

    def __repr__(self):
        return self.message


class InvalidVariableNameException(ScratchRuntimeException):
    def __init__(self, var_name):
        super().__init__(f'Invalid variable {var_name}')


class EmptyArgumentException(ScratchRuntimeException):
    def __init__(self):
        super().__init__('Empty argument')


class InvalidNumberException(ScratchRuntimeException):
    def __init__(self):
        super().__init__('Invalid number')
