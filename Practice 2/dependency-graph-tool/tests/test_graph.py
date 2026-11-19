"""Тесты DFS, глубины, циклов и порядка загрузки."""

import pytest

from graph import GraphCycleError, build_graph, compute_load_order

ONE_CALL = 1


def test_build_graph_without_cycle() -> None:
    """DFS добавляет прямые и транзитивные зависимости."""
    data = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
    graph, cycles = build_graph("A", data.get, 10)
    assert graph["A"] == ["B", "C"]
    assert graph["D"] == []
    assert cycles == []


def test_build_graph_detects_cycle() -> None:
    """Циклическое ребро обнаруживается, обход завершается."""
    data = {"A": ["B"], "B": ["C"], "C": ["A", "D"], "D": []}
    graph, cycles = build_graph("A", data.get, 10)
    assert ("C", "A") in cycles
    assert set(graph) == {"A", "B", "C", "D"}


def test_max_depth_stops_expansion() -> None:
    """Узел на предельной глубине не раскрывается дальше."""
    data = {"A": ["B"], "B": ["C"], "C": ["D"], "D": []}
    graph, _ = build_graph("A", data.get, 2)
    assert graph["C"] == []
    assert "D" not in graph


def test_shorter_path_reopens_node() -> None:
    """Короткий путь раскрывает узел после посещения по длинному."""
    data = {
        "A": ["C", "B"], "C": ["E"], "E": ["D"],
        "B": ["D"], "D": ["F"], "F": [],
    }
    graph, cycles = build_graph("A", data.get, 3)
    assert graph["D"] == ["F"]
    assert "F" in graph
    assert cycles == []


def test_zero_depth_keeps_only_root() -> None:
    """При нулевой глубине остаётся один корневой узел."""
    graph, cycles = build_graph("A", lambda node: ["B"], 0)
    assert graph == {"A": []}
    assert cycles == []


def test_load_order_places_dependencies_first() -> None:
    """Зависимость появляется раньше пакета, который её использует."""
    graph = {"A": ["B", "C"], "B": ["C"], "C": []}
    order = compute_load_order(graph, "A")
    assert order.index("C") < order.index("B")
    assert order.index("B") < order.index("A")


def test_load_order_rejects_cycle() -> None:
    """Для циклического графа нельзя вернуть порядок загрузки."""
    graph = {"A": ["B"], "B": ["A"]}
    with pytest.raises(GraphCycleError):
        compute_load_order(graph, "A")


def test_dependencies_are_loaded_once() -> None:
    """Повторный короткий путь не скачивает данные узла второй раз."""
    data = {
        "A": ["C", "B"], "C": ["E"], "E": ["D"],
        "B": ["D"], "D": ["F"], "F": [],
    }
    calls = {}

    def get_deps(node: str) -> list[str]:
        """Считает запросы зависимостей каждого узла."""
        calls[node] = calls.get(node, 0) + ONE_CALL
        return data.get(node, [])

    build_graph("A", get_deps, 3)
    assert calls["D"] == ONE_CALL
