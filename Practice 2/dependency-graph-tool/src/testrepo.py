"""Загрузка тестового графа из обычного текстового файла."""

from __future__ import annotations

import os
import re


class RepositoryFormatError(Exception):
    """Ошибка формата тестового репозитория."""


def _valid_name(name: str) -> bool:
    """Проверяет имя узла по условию задания."""
    return re.fullmatch(r"[A-Z]+", name) is not None


def _parse_line(line: str, number: int) -> tuple[str, list[str]]:
    """Разбирает одну запись тестового графа."""
    node, separator, text = line.partition(":")
    node = node.strip()
    if not separator or not _valid_name(node):
        raise RepositoryFormatError(
            f"Строка {number}: ожидается формат 'A: B C'.")
    deps = text.split()
    if any(not _valid_name(dep) for dep in deps):
        raise RepositoryFormatError(
            f"Строка {number}: имя зависимости должно быть A-Z.")
    return node, list(dict.fromkeys(deps))


def _add_leaf_nodes(graph: dict[str, list[str]]) -> None:
    """Добавляет в граф зависимости без собственных зависимостей."""
    for deps in list(graph.values()):
        for dep in deps:
            graph.setdefault(dep, [])


def load_graph(path: str) -> dict[str, list[str]]:
    """Читает строки вида 'A: B C' и возвращает список зависимостей."""
    if not os.path.isfile(path):
        raise RepositoryFormatError(f"Файл не найден: {path}")
    graph: dict[str, list[str]] = {}
    with open(path, encoding="utf-8") as file:
        for number, raw in enumerate(file, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            node, deps = _parse_line(line, number)
            if node in graph:
                raise RepositoryFormatError(
                    f"Строка {number}: узел {node} уже задан.")
            graph[node] = deps
    _add_leaf_nodes(graph)
    return graph
