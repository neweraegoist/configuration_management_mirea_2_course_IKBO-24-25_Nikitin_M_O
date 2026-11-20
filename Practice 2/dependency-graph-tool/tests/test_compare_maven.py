"""Тесты сравнения с выводом Maven dependency:tree."""

from types import SimpleNamespace
from xml.etree.ElementTree import fromstring

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
    monkeypatch.setattr(
        compare_maven.subprocess, "run", lambda *a, **k: result)
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


def test_parse_real_maven_root_and_classifier() -> None:
    """Читает корень без scope и зависимость с classifier."""
    output = """\
[INFO] mirea.check:compare:jar:1.0
[INFO] \\- org.demo:app:jar:1.0:compile
[INFO]    \\- org.demo:native:jar:linux-x86_64:2.0:runtime
"""
    assert parse_maven_tree(output) == [
        "mirea.check:compare:1.0",
        "org.demo:app:1.0",
        "org.demo:native:2.0",
    ]


@pytest.mark.parametrize("deps", [[], ["org.demo:first:2.0"]])
def test_compare_excludes_checked_package(monkeypatch, deps) -> None:
    """Сравнивает зависимости без временного POM и проверяемого пакета."""
    tree = (
        "[INFO] mirea.check:compare:jar:1.0\n"
        "[INFO] \\- org.demo:app:jar:1.0:compile\n"
    )
    if deps:
        tree += "[INFO]    \\- org.demo:first:jar:2.0:compile\n"
    result = SimpleNamespace(returncode=SUCCESS, stdout=tree, stderr="")
    monkeypatch.setattr(compare_maven.shutil, "which", lambda name: "/mvn")
    monkeypatch.setattr(
        compare_maven.subprocess, "run", lambda *args, **kwargs: result)
    pkg = MavenPackage("org.demo", "app", "1.0")
    _, only_ours, only_maven = compare_with_maven(
        pkg, "https://repo.example", deps + [pkg.id])
    assert only_ours == []
    assert only_maven == []


def test_comparison_pom_escapes_repository_query(monkeypatch) -> None:
    """Создаёт корректный XML для адреса репозитория с амперсандом."""
    repository = "https://repo.example/maven?first=1&second=2"
    result = SimpleNamespace(returncode=SUCCESS, stdout="", stderr="")

    def run_maven(args, **kwargs):
        """Проверяет временный POM перед подменённым запуском Maven."""
        xml = compare_maven.Path(args[2]).read_text(encoding="utf-8")
        root = fromstring(xml)
        namespace = {"m": "http://maven.apache.org/POM/4.0.0"}
        node = root.find("m:repositories/m:repository/m:url", namespace)
        assert node.text == repository
        return result

    monkeypatch.setattr(compare_maven.shutil, "which", lambda name: "/mvn")
    monkeypatch.setattr(compare_maven.subprocess, "run", run_maven)
    pkg = MavenPackage("org.demo", "app", "1.0")
    compare_with_maven(pkg, repository, [pkg.id])
