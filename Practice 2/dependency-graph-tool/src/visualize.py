"""Формирование PlantUML и ASCII-представления графа."""

from __future__ import annotations


def to_plantuml(graph: dict[str, list[str]]) -> str:
    """Создаёт текст PlantUML с отдельным alias для каждого пакета."""
    nodes = list(graph)
    names = {node: f"N{index}" for index, node in enumerate(nodes)}
    lines = ["@startuml", "left to right direction"]
    for node in nodes:
        safe = node.replace('"', "'")
        lines.append(f'rectangle "{safe}" as {names[node]}')
    for node, deps in graph.items():
        for dep in deps:
            if dep in names:
                lines.append(f"{names[node]} --> {names[dep]}")
    lines.append("@enduml")
    return "\n".join(lines)


def to_ascii_tree(graph: dict[str, list[str]], root: str) -> str:
    """Печатает дерево и отмечает циклы, не раскрывая их повторно."""
    if root not in graph:
        return ""
    lines = [root]
    stack = []
    deps = graph.get(root, [])
    for index, dep in reversed(list(enumerate(deps))):
        stack.append((dep, "", index == len(deps) - 1, (root,)))
    while stack:
        node, prefix, last, path = stack.pop()
        mark = "└── " if last else "├── "
        is_cycle = node in path
        suffix = " (цикл)" if is_cycle else ""
        lines.append(prefix + mark + node + suffix)
        if is_cycle:
            continue
        child_prefix = prefix + ("    " if last else "│   ")
        children = graph.get(node, [])
        for index, dep in reversed(list(enumerate(children))):
            stack.append((dep, child_prefix, index == len(children) - 1,
                          path + (node,)))
    return "\n".join(lines)
