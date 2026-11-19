"""Проверка работы приложения по этапам."""

from pathlib import Path

from main import run

EXAMPLES = Path(__file__).parents[1] / "examples"
SUCCESS = 0
FAILURE = 1
STAGE_CONFIG = 1
STAGE_DIRECT = 2
STAGE_GRAPH = 3
STAGE_ORDER = 4
STAGE_VISUAL = 5


def test_stage_one_prints_configuration(capsys) -> None:
    """Первый этап показывает шесть параметров."""
    result = run(str(EXAMPLES / "config_test_simple.xml"), STAGE_CONFIG)
    output = capsys.readouterr().out
    assert result == SUCCESS
    assert "package_name=A" in output
    assert "max_depth=10" in output


def test_stage_two_prints_direct_dependencies(capsys) -> None:
    """Второй этап показывает только прямые зависимости корня."""
    result = run(str(EXAMPLES / "config_test_simple.xml"), STAGE_DIRECT)
    output = capsys.readouterr().out
    assert result == SUCCESS
    assert "Прямые зависимости A" in output
    assert "- B" in output
    assert "- C" in output


def test_stage_three_shows_cycles(capsys) -> None:
    """Третий этап выводит циклические рёбра."""
    result = run(str(EXAMPLES / "config_test_cycle.xml"), STAGE_GRAPH)
    output = capsys.readouterr().out
    assert result == SUCCESS
    assert "Циклические рёбра" in output


def test_stage_four_refuses_cycle(capsys) -> None:
    """Четвёртый этап не выдаёт порядок для графа с циклом."""
    result = run(str(EXAMPLES / "config_test_cycle.xml"), STAGE_ORDER)
    output = capsys.readouterr().err
    assert result == FAILURE
    assert "цикл" in output.lower()


def test_stage_five_prints_plantuml(capsys) -> None:
    """Пятый этап выводит диаграмму и ASCII-дерево."""
    result = run(str(EXAMPLES / "config_test_simple.xml"), STAGE_VISUAL)
    output = capsys.readouterr().out
    assert result == SUCCESS
    assert "@startuml" in output
    assert "@enduml" in output
    assert "ASCII-дерево" in output
