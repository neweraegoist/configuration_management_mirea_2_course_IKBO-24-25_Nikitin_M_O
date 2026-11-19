"""Тесты вывода PlantUML и ASCII-дерева."""

from visualize import to_ascii_tree, to_plantuml

TWO = 2


def test_plantuml_has_nodes_and_edges() -> None:
    """PlantUML содержит заголовок, узлы, связи и конец диаграммы."""
    graph = {"A": ["B", "C"], "B": [], "C": []}
    text = to_plantuml(graph)
    assert text.startswith("@startuml")
    assert text.endswith("@enduml")
    assert 'rectangle "A" as N0' in text
    assert "N0 --> N1" in text
    assert "N0 --> N2" in text


def test_plantuml_contains_isolated_node() -> None:
    """Отдельный пакет без зависимостей остаётся на диаграмме."""
    assert 'rectangle "A" as N0' in to_plantuml({"A": []})


def test_ascii_tree_marks_cycle() -> None:
    """Дерево помечает цикл и прекращает его раскрытие."""
    graph = {"A": ["B"], "B": ["A"]}
    text = to_ascii_tree(graph, "A")
    assert text.splitlines()[0] == "A"
    assert "B" in text
    assert "цикл" in text


def test_ascii_tree_shows_shared_node() -> None:
    """Общий узел показывается под обоими родителями."""
    graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
    text = to_ascii_tree(graph, "A")
    assert text.count("D") == TWO
