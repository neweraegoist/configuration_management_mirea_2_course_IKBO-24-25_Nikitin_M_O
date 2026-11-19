"""Тесты загрузчика тестового графа."""

from pathlib import Path

import pytest

from testrepo import RepositoryFormatError, load_graph

EXAMPLES = Path(__file__).parents[1] / "examples"


def test_load_simple_graph() -> None:
    """Зависимости и пустые узлы считываются правильно."""
    graph = load_graph(str(EXAMPLES / "test_repo_simple.txt"))
    assert graph["A"] == ["B", "C"]
    assert graph["D"] == []


def test_load_cycle_graph() -> None:
    """Файл с циклом загружается, чтобы его проверил обход графа."""
    graph = load_graph(str(EXAMPLES / "test_repo_cycle.txt"))
    assert graph["C"] == ["A", "D"]


def test_missing_file() -> None:
    """Отсутствующий файл вызывает ошибку."""
    with pytest.raises(RepositoryFormatError):
        load_graph(str(EXAMPLES / "not_found.txt"))


def test_bad_line(tmp_path: Path) -> None:
    """Строка без двоеточия не принимается."""
    path = tmp_path / "bad.txt"
    path.write_text("incorrect line\n", encoding="utf-8")
    with pytest.raises(RepositoryFormatError):
        load_graph(str(path))


def test_lowercase_node(tmp_path: Path) -> None:
    """Имена узлов должны состоять из заглавных латинских букв."""
    path = tmp_path / "bad.txt"
    path.write_text("a: B\n", encoding="utf-8")
    with pytest.raises(RepositoryFormatError):
        load_graph(str(path))


def test_duplicate_node(tmp_path: Path) -> None:
    """Повторное объявление узла вызывает ошибку."""
    path = tmp_path / "duplicate.txt"
    path.write_text("A: B\nA: C\n", encoding="utf-8")
    with pytest.raises(RepositoryFormatError, match="уже задан"):
        load_graph(str(path))
