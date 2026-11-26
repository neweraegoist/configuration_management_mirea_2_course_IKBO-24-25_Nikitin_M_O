"""Syntax parser built with the Lark parsing library."""

from dataclasses import dataclass
from typing import Any

from lark import Lark, Transformer, UnexpectedInput

from src.errors import ConfigError


GRAMMAR = r"""
start: global_decl* dictionary

global_decl: "global" NAME "=" value ";"

?value: HEX                         -> number
      | dictionary
      | "{" expression "}"         -> expression_value

dictionary: "dict" "(" [pair ("," pair)* [","]] ")"
pair: NAME "=" value

?expression: sum
?sum: sum "+" product             -> add
    | sum "-" product             -> subtract
    | product
?product: product "*" atom        -> multiply
        | product "/" atom        -> divide
        | atom
?atom: HEX                         -> number
     | NAME                        -> variable
     | "sqrt" "(" expression ")"  -> square_root
     | "mod" "(" expression "," expression ")" -> modulo
     | "(" expression ")"

HEX: /0[xX][0-9a-fA-F]+/
NAME: /[a-zA-Z]+/
COMMENT: /\/\+[\s\S]*?\+\//
%ignore COMMENT
%ignore /[ \t\f\r\n]+/
"""


@dataclass
class DictionaryNode:
    """A dictionary keeps pairs until duplicate keys can be checked."""

    entries: list[tuple[str, Any]]


@dataclass
class Program:
    """Parsed declarations and the root configuration dictionary."""

    declarations: list[tuple[str, Any]]
    config: DictionaryNode


class BuildAst(Transformer):
    """Convert the Lark parse tree into a small syntax tree."""

    def start(self, items: list[Any]) -> Program:
        return Program(items[:-1], items[-1])

    def global_decl(self, items: list[Any]) -> tuple[str, Any]:
        return str(items[0]), items[1]

    def number(self, items: list[Any]) -> int:
        return int(str(items[0]), 16)

    def expression_value(self, items: list[Any]) -> Any:
        return items[0]

    def pair(self, items: list[Any]) -> tuple[str, Any]:
        return str(items[0]), items[1]

    def dictionary(self, items: list[Any]) -> DictionaryNode:
        return DictionaryNode(items)

    def variable(self, items: list[Any]) -> tuple[str, Any]:
        return "variable", str(items[0])

    def add(self, items: list[Any]) -> tuple[str, Any, Any]:
        return "add", items[0], items[1]

    def subtract(self, items: list[Any]) -> tuple[str, Any, Any]:
        return "subtract", items[0], items[1]

    def multiply(self, items: list[Any]) -> tuple[str, Any, Any]:
        return "multiply", items[0], items[1]

    def divide(self, items: list[Any]) -> tuple[str, Any, Any]:
        return "divide", items[0], items[1]

    def square_root(self, items: list[Any]) -> tuple[str, Any]:
        return "sqrt", items[0]

    def modulo(self, items: list[Any]) -> tuple[str, Any, Any]:
        return "mod", items[0], items[1]


_PARSER = Lark(GRAMMAR, parser="lalr", start="start")
_BUILDER = BuildAst()


def parse_source(source: str) -> Program:
    """Parse source text and return its syntax tree."""
    try:
        tree = _PARSER.parse(source)
        return _BUILDER.transform(tree)
    except UnexpectedInput as error:
        line = getattr(error, "line", 1)
        column = getattr(error, "column", 1)
        message = (
            f"Синтаксическая ошибка: строка {line}, "
            f"столбец {column}."
        )
        raise ConfigError(message) from error
    except ConfigError:
        raise
    except Exception as error:
        message = "Ошибка разбора: "
        raise ConfigError(message + str(error)) from error
