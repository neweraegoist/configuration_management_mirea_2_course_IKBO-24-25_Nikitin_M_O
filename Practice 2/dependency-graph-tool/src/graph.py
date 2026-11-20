"""Построение графа итеративным DFS и расчёт порядка загрузки."""

from __future__ import annotations

from typing import Callable


UNVISITED = 0
ACTIVE = 1
DONE = 2
ROOT_DEPTH = 0
FIRST_INDEX = 0


class GraphCycleError(Exception):
    """Порядок загрузки нельзя построить из-за цикла."""


def _unique(values: list[str]) -> list[str]:
    """Убирает повторяющиеся зависимости, сохраняя их порядок."""
    return list(dict.fromkeys(values))


def _find_cycles(graph: dict[str, list[str]]) -> list[tuple[str, str]]:
    """Находит рёбра, замыкающие циклы, без рекурсивных вызовов."""
    colors = {node: UNVISITED for node in graph}
    cycles: list[tuple[str, str]] = []
    for start in graph:
        if colors[start] != UNVISITED:
            continue
        colors[start] = ACTIVE
        stack = [(start, FIRST_INDEX)]
        while stack:
            node, index = stack[-1]
            deps = graph[node]
            if index == len(deps):
                colors[node] = DONE
                stack.pop()
                continue
            dep = deps[index]
            stack[-1] = (node, index + 1)
            if colors.get(dep, UNVISITED) == ACTIVE:
                cycles.append((node, dep))
            elif colors.get(dep, UNVISITED) == UNVISITED:
                colors[dep] = ACTIVE
                stack.append((dep, FIRST_INDEX))
    return cycles


def build_graph(
    root: str,
    get_deps: Callable[[str], list[str]],
    max_depth: int,
) -> tuple[dict[str, list[str]], list[tuple[str, str]]]:
    """Строит транзитивный граф поиском в глубину без рекурсии.

    Узел раскрывается повторно, если найден путь короче предыдущего.
    Благодаря этому ограничение глубины не теряет доступные зависимости.
    """
    if max_depth < ROOT_DEPTH:
        raise ValueError("max_depth не может быть отрицательным.")
    graph: dict[str, list[str]] = {root: []}
    best_depth: dict[str, int] = {}
    deps_cache: dict[str, list[str]] = {}
    stack = [(root, ROOT_DEPTH)]
    while stack:
        node, depth = stack.pop()
        if node in best_depth and best_depth[node] <= depth:
            continue
        best_depth[node] = depth
        graph.setdefault(node, [])
        if depth >= max_depth:
            continue
        if node not in deps_cache:
            deps_cache[node] = _unique(get_deps(node))
        deps = deps_cache[node]
        graph[node] = deps
        for dep in reversed(deps):
            graph.setdefault(dep, [])
            stack.append((dep, depth + 1))
    return graph, _find_cycles(graph)


def compute_load_order(graph: dict[str, list[str]], root: str) -> list[str]:
    """Возвращает зависимости раньше пакетов, которые от них зависят."""
    if root not in graph:
        raise ValueError(f"Корневой пакет {root} отсутствует в графе.")
    colors = {node: UNVISITED for node in graph}
    order: list[str] = []
    colors[root] = ACTIVE
    stack = [(root, ROOT_DEPTH)]
    while stack:
        node, index = stack[-1]
        deps = graph[node]
        if index == len(deps):
            colors[node] = DONE
            order.append(node)
            stack.pop()
            continue
        dep = deps[index]
        stack[-1] = (node, index + 1)
        state = colors.get(dep, UNVISITED)
        if state == ACTIVE:
            raise GraphCycleError(f"Обнаружен цикл: {node} -> {dep}.")
        if state == UNVISITED:
            colors[dep] = ACTIVE
            stack.append((dep, FIRST_INDEX))
    return order
