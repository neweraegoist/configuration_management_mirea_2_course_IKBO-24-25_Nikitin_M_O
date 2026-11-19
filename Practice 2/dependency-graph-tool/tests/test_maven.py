"""Тесты самостоятельного разбора Maven POM."""

import pytest

from maven import MavenError, MavenPackage, parse_direct_dependencies


POM = """\
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <properties><dep.version>2.5.0</dep.version></properties>
  <dependencyManagement><dependencies>
    <dependency><groupId>test</groupId><artifactId>managed</artifactId>
      <version>${dep.version}</version></dependency>
  </dependencies></dependencyManagement>
  <dependencies>
    <dependency><groupId>test</groupId><artifactId>first</artifactId>
      <version>${dep.version}</version></dependency>
    <dependency><groupId>test</groupId><artifactId>managed</artifactId>
    </dependency>
    <dependency><groupId>test</groupId><artifactId>test-only</artifactId>
      <version>1.0</version><scope>test</scope></dependency>
    <dependency><groupId>test</groupId><artifactId>optional</artifactId>
      <version>1.0</version><optional>true</optional></dependency>
  </dependencies>
</project>
"""


def test_parse_direct_dependencies() -> None:
    """Читаются compile-зависимости с явной и управляемой версией."""
    pkg = MavenPackage("sample", "app", "1.0")
    deps = parse_direct_dependencies(POM, pkg)
    assert [item.id for item in deps] == [
        "test:first:2.5.0", "test:managed:2.5.0"]


def test_parse_package_coordinates() -> None:
    """Координаты Maven разбираются из трёх частей."""
    pkg = MavenPackage.parse("org.demo:demo:1.2.3")
    assert pkg.group_id == "org.demo"
    assert pkg.id == "org.demo:demo:1.2.3"


def test_invalid_package_coordinates() -> None:
    """Неверные координаты вызывают MavenError."""
    with pytest.raises(MavenError):
        MavenPackage.parse("wrong-format")


def test_invalid_pom() -> None:
    """Повреждённый POM не приводит к необработанному исключению."""
    pkg = MavenPackage("sample", "app", "1.0")
    with pytest.raises(MavenError, match="Некорректный"):
        parse_direct_dependencies("<project>", pkg)


def test_pom_without_dependencies() -> None:
    """POM без прямых зависимостей возвращает пустой список."""
    pkg = MavenPackage("sample", "empty", "1.0")
    result = parse_direct_dependencies("<project />", pkg)
    assert result == []


def test_fetch_pom_uses_repository_path(monkeypatch) -> None:
    """POM загружается по стандартному пути Maven-репозитория."""
    import maven

    class Response:
        """Небольшой ответ HTTP для теста без сети."""

        def __enter__(self):
            """Возвращает объект ответа."""
            return self

        def __exit__(self, *args):
            """Закрывает тестовый контекст без подавления ошибок."""
            return False

        def read(self):
            """Возвращает содержимое тестового POM."""
            return b"<project />"

    saved = {}

    def fake_open(request, timeout):
        """Запоминает адрес запроса и возвращает тестовый ответ."""
        saved["url"] = request.full_url
        saved["timeout"] = timeout
        return Response()

    monkeypatch.setattr(maven.urllib.request, "urlopen", fake_open)
    pkg = MavenPackage("org.demo", "sample", "1.0")
    result = maven.fetch_pom("https://repo.example/maven2", pkg)
    assert result == "<project />"
    assert saved["url"] == (
        "https://repo.example/maven2/org/demo/sample/1.0/sample-1.0.pom")


def test_fetch_pom_http_error(monkeypatch) -> None:
    """HTTP-ошибка преобразуется в MavenError."""
    import urllib.error
    import maven

    def fake_open(request, timeout):
        """Возвращает HTTP 404 для проверки обработки ошибки."""
        raise urllib.error.HTTPError(
            request.full_url, 404, "Not found", {}, None)

    monkeypatch.setattr(maven.urllib.request, "urlopen", fake_open)
    pkg = MavenPackage("org.demo", "missing", "1.0")
    with pytest.raises(MavenError, match="HTTP 404"):
        maven.fetch_pom("https://repo.example", pkg)


def test_get_dependencies_inherits_parent_settings(monkeypatch) -> None:
    """Родительские свойства и зависимости доступны дочернему POM."""
    import maven

    child = """\
<project>
  <parent><groupId>sample</groupId><artifactId>parent</artifactId>
    <version>1.0</version></parent>
  <groupId>sample</groupId><artifactId>app</artifactId><version>2.0</version>
  <dependencies><dependency><groupId>lib</groupId>
    <artifactId>managed</artifactId></dependency></dependencies>
</project>
"""
    parent = """\
<project>
  <groupId>sample</groupId><artifactId>parent</artifactId><version>1.0</version>
  <properties><managed.version>3.0</managed.version></properties>
  <dependencyManagement><dependencies><dependency>
    <groupId>lib</groupId><artifactId>managed</artifactId>
    <version>${managed.version}</version>
  </dependency></dependencies></dependencyManagement>
  <dependencies><dependency><groupId>base</groupId>
    <artifactId>parent-lib</artifactId><version>4.0</version>
  </dependency></dependencies>
</project>
"""
    files = {
        "sample:app:2.0": child,
        "sample:parent:1.0": parent,
    }
    monkeypatch.setattr(
        maven, "fetch_pom", lambda repository, pkg: files[pkg.id])
    pkg = MavenPackage("sample", "app", "2.0")
    deps = maven.get_direct_dependencies("https://repo.example", pkg)
    assert [item.id for item in deps] == [
        "base:parent-lib:4.0", "lib:managed:3.0"]
