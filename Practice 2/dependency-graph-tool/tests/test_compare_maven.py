"""Тесты сравнения с выводом Maven dependency:tree."""

from types import SimpleNamespace

import pytest

import compare_maven
from compare_maven import compare_with_maven, parse_maven_tree
from maven import MavenError, MavenPackage

SUCCESS = 0


def test_parse_maven_tree() -> None:
    """Координаты зависимостей извлекаются из стандартного вывода."""
    output = """\
[INFO] sample:application:jar:1.0:compile
[INFO] +- org.demo:first:jar:2.0:compile
[INFO] |  \\- org.demo:second:jar:3.0:runtime
"""
    result = parse_maven_tree(output)
    assert result == [
        "sample:application:1.0",
        "org.demo:first:2.0",
        "org.demo:second:3.0",
    ]


def test_compare_with_maven(monkeypatch) -> None:
    """Сравнение возвращает совпавшие и отличающиеся зависимости."""
    tree = """\
[INFO] sample:compare:jar:1.0:compile
[INFO] +- org.demo:first:jar:2.0:compile
"""
    result = SimpleNamespace(returncode=SUCCESS, stdout=tree, stderr="")
    monkeypatch.setattr(compare_maven.shutil, "which", lambda name: "/mvn")
    monkeypatch.setattr(compare_maven.subprocess, "run", lambda *a, **k: result)
    pkg = MavenPackage("org.demo", "app", "1.0")
    data = compare_with_maven(pkg, "https://repo.example", [
        "org.demo:first:2.0", pkg.id])
    assert data == (["sample:compare:1.0", "org.demo:first:2.0"], [], [])


def test_compare_without_maven(monkeypatch) -> None:
    """При отсутствии команды Maven выводится понятная ошибка."""
    monkeypatch.setattr(compare_maven.shutil, "which", lambda name: None)
    pkg = MavenPackage("org.demo", "app", "1.0")
    with pytest.raises(MavenError, match="не найдена"):
        compare_with_maven(pkg, "https://repo.example", [pkg.id])
