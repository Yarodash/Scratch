from typing import *

import useful
import scratch_exceptions


class Value:

    @classmethod
    def get_type_name(cls) -> str:
        return cls.__name__

    def get_value(self):
        raise NotImplementedError


class VariableScope:

    def __init__(self):
        self.variables: dict[str, Value] = {}

    def set_variable(self, var_name: str, value: Value) -> None:
        self.variables[var_name] = value

    def get_variable(self, var_name: str) -> Value:
        try:
            return self.variables[var_name]
        except KeyError:
            raise scratch_exceptions.InvalidVariableName


class ReturnsValue:

    def calculate(self, variable_scope: VariableScope) -> Value:
        raise NotImplementedError


class Integer(Value):

    def __init__(self, value: int):
        self.value: int = value

    def get_value(self) -> int:
        return self.value


class ReturnsInteger(ReturnsValue):

    def calculate(self, variable_scope: VariableScope) -> Integer:
        raise NotImplementedError


class IntegerBlock(ReturnsInteger):

    def __init__(self, text: str):
        self.text: str = text

    def set_text(self, new_text: str) -> None:
        self.text = new_text

    def get_text(self) -> str:
        return self.text

    def calculate(self, variable_scope: VariableScope) -> Integer:
        if useful.represents_integer(self.text):
            return Integer(int(self.text))

        variable_value = variable_scope.get_variable(self.text)
        if not isinstance(variable_value, Integer):
            raise scratch_exceptions.TypeMismatch(Integer, variable_value.__class__)

        return variable_value


class Boolean(Value):

    def __init__(self, value: bool):
        self.value: bool = value

    def get_value(self) -> bool:
        return self.value


class ReturnsBoolean(ReturnsValue):

    def calculate(self, variable_scope: VariableScope) -> Boolean:
        raise NotImplementedError


class BooleanBlock(ReturnsBoolean):

    def __init__(self, text: str):
        self.text: str = text

    def set_text(self, new_text: str) -> None:
        self.text = new_text

    def get_text(self) -> str:
        return self.text

    def calculate(self, variable_scope: VariableScope) -> Boolean:
        if self.text == 'true':
            return Boolean(True)

        if self.text == 'false':
            return Boolean(False)

        variable_value = variable_scope.get_variable(self.text)
        if not isinstance(variable_value, Boolean):
            raise scratch_exceptions.TypeMismatch(Integer, variable_value.__class__)

        return variable_value
