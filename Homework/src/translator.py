"""Compile parsed configuration values and convert them to YAML."""

import math
from typing import Any, Union

import yaml

from src.errors import ConfigError
from src.parser import DictionaryNode, Program, parse_source

ZERO = 0


def _check_number(value: Any) -> Union[int, float]:
    """Return a numeric value or raise a readable error."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        message = (
            "В арифметическом выражении "
            "ожидалось число."
        )
        raise ConfigError(message)
    return value


def _resolve_variable(name: str, constants: dict[str, Any]) -> Any:
    """Get a previously declared constant."""
    if name not in constants:
        raise ConfigError(
            f"Константа '{name}' "
            "не объявлена."
        )
    return constants[name]


def _evaluate_sqrt(node: Any, constants: dict[str, Any]) -> float:
    """Evaluate the square-root function."""
    value = _check_number(_evaluate_expression(node, constants))
    if value < ZERO:
        message = (
            "Нельзя извлечь корень "
            "из отрицательного числа."
        )
        raise ConfigError(message)
    return math.sqrt(value)


def _evaluate_binary(node: Any, constants: dict[str, Any]) -> Union[int, float]:
    """Evaluate a binary arithmetic operation."""
    operation = node[0]
    left = _check_number(_evaluate_expression(node[1], constants))
    right = _check_number(_evaluate_expression(node[2], constants))
    if operation == "add":
        return left + right
    if operation == "subtract":
        return left - right
    if operation == "multiply":
        return left * right
    if operation == "divide":
        if right == ZERO:
            raise ConfigError("Деление на ноль.")
        return left / right
    if operation == "mod":
        if right == ZERO:
            raise ConfigError(
                "Остаток от деления на ноль."
            )
        return left % right
    raise ConfigError(
        "Неизвестная операция в выражении."
    )


def _evaluate_expression(node: Any, constants: dict[str, Any]) -> Any:
    """Calculate an expression without using eval()."""
    if not isinstance(node, tuple):
        return node
    operation = node[0]
    if operation == "variable":
        return _resolve_variable(node[1], constants)
    if operation == "sqrt":
        return _evaluate_sqrt(node[1], constants)
    return _evaluate_binary(node, constants)


def _resolve_value(value: Any, constants: dict[str, Any]) -> Any:
    """Resolve expressions and nested dictionaries recursively."""
    if isinstance(value, DictionaryNode):
        result: dict[str, Any] = {}
        for name, child in value.entries:
            if name in result:
                raise ConfigError(
                    f"Ключ '{name}' "
                    "повторяется в словаре."
                )
            result[name] = _resolve_value(child, constants)
        return result
    return _evaluate_expression(value, constants)


def compile_program(program: Program) -> dict[str, Any]:
    """Evaluate constants in order and compile the root dictionary."""
    constants: dict[str, Any] = {}
    for name, value in program.declarations:
        if name in constants:
            raise ConfigError(
                f"Константа '{name}' "
                "объявлена повторно."
            )
        constants[name] = _resolve_value(value, constants)

    result = _resolve_value(program.config, constants)
    if not isinstance(result, dict):
        message = (
            "Корневое значение должно быть "
            "словарём dict(...)."
        )
        raise ConfigError(message)
    return result


def translate(source: str) -> str:
    """Translate source configuration text into YAML text."""
    program = parse_source(source)
    result = compile_program(program)
    return yaml.safe_dump(
        result,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )
