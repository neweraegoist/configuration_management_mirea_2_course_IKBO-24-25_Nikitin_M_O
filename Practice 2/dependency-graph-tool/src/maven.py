"""Получение прямых зависимостей из Maven POM без Maven-библиотек."""

from __future__ import annotations

import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass

EXPECTED_COORDINATE_PARTS = 3
MAX_PARENT_DEPTH = 10


class MavenError(Exception):
    """Ошибка загрузки или разбора Maven POM."""


@dataclass(frozen=True)
class MavenPackage:
    """Координаты Maven-пакета."""

    group_id: str
    artifact_id: str
    version: str

    @property
    def id(self) -> str:
        """Возвращает координаты в формате group:artifact:version."""
        return f"{self.group_id}:{self.artifact_id}:{self.version}"

    @staticmethod
    def parse(value: str) -> "MavenPackage":
        """Разбирает координаты Maven-пакета."""
        parts = value.split(":")
        if len(parts) != EXPECTED_COORDINATE_PARTS or not all(parts):
            raise MavenError(f"Неверные координаты Maven-пакета: {value}")
        return MavenPackage(*parts)


@dataclass
class PomContext:
    """Свойства, управляемые версии и зависимости POM."""

    props: dict[str, str]
    managed: dict[str, str]
    dependencies: list[MavenPackage]


def _local(tag: str) -> str:
    """Убирает пространство имён из XML-тега."""
    return tag.rsplit("}", 1)[-1]


def _child(parent: ET.Element, name: str) -> ET.Element | None:
    """Находит прямой дочерний XML-элемент по имени."""
    return next((item for item in parent if _local(item.tag) == name), None)


def _text(parent: ET.Element, name: str) -> str:
    """Читает текст прямого дочернего XML-элемента."""
    node = _child(parent, name)
    return (node.text or "").strip() if node is not None else ""


def _read_root(pom_text: str) -> ET.Element:
    """Преобразует текст POM в XML-дерево."""
    try:
        return ET.fromstring(pom_text)
    except ET.ParseError as error:
        raise MavenError(f"Некорректный pom.xml: {error}") from error


def _resolve(value: str, props: dict[str, str]) -> str:
    """Подставляет свойства Maven, например ${project.version}."""
    pattern = re.compile(r"\$\{([^}]+)\}")
    for _ in range(MAX_PARENT_DEPTH):
        match = pattern.search(value)
        if match is None:
            return value.strip()
        replacement = props.get(match.group(1))
        if replacement is None:
            return ""
        value = value[:match.start()] + replacement + value[match.end():]
    return ""


def _properties(
    root: ET.Element,
    pkg: MavenPackage,
    inherited: dict[str, str],
) -> dict[str, str]:
    """Собирает свойства POM с учётом свойств родительского файла."""
    props = dict(inherited)
    props.update({
        "project.groupId": pkg.group_id,
        "pom.groupId": pkg.group_id,
        "project.artifactId": pkg.artifact_id,
        "pom.artifactId": pkg.artifact_id,
        "project.version": pkg.version,
        "pom.version": pkg.version,
    })
    parent = _child(root, "parent")
    if parent is not None:
        props["project.parent.groupId"] = _text(parent, "groupId")
        props["project.parent.artifactId"] = _text(parent, "artifactId")
        props["project.parent.version"] = _text(parent, "version")
    node = _child(root, "properties")
    names = []
    if node is not None:
        for item in node:
            name = _local(item.tag)
            props[name] = (item.text or "").strip()
            names.append(name)
    for name in names:
        props[name] = _resolve(props[name], props)
    return props


def _managed_versions(
    root: ET.Element, props: dict[str, str],
) -> dict[str, str]:
    """Читает версии из dependencyManagement текущего POM."""
    result: dict[str, str] = {}
    manager = _child(root, "dependencyManagement")
    deps = _child(manager, "dependencies") if manager is not None else None
    if deps is None:
        return result
    for item in deps:
        group = _resolve(_text(item, "groupId"), props)
        artifact = _resolve(_text(item, "artifactId"), props)
        version = _resolve(_text(item, "version"), props)
        if group and artifact and version:
            result[f"{group}:{artifact}"] = version
    return result


def _is_allowed(item: ET.Element, props: dict[str, str]) -> bool:
    """Отбрасывает необязательные и нерабочие области зависимостей."""
    scope = _resolve(_text(item, "scope") or "compile", props)
    optional = _resolve(_text(item, "optional") or "false", props)
    excluded = {"test", "provided", "system", "import"}
    return scope not in excluded and optional.lower() != "true"


def _parse_dependency(
    item: ET.Element,
    props: dict[str, str],
    managed: dict[str, str],
) -> MavenPackage | None:
    """Преобразует один XML-элемент dependency в координаты пакета."""
    if not _is_allowed(item, props):
        return None
    group = _resolve(_text(item, "groupId"), props)
    artifact = _resolve(_text(item, "artifactId"), props)
    version = _resolve(_text(item, "version"), props)
    if not version:
        version = managed.get(f"{group}:{artifact}", "")
    if not group or not artifact or not version:
        return None
    return MavenPackage(group, artifact, version)


def _direct_dependencies(
    root: ET.Element,
    props: dict[str, str],
    managed: dict[str, str],
) -> list[MavenPackage]:
    """Читает прямые зависимости из раздела dependencies."""
    deps_node = _child(root, "dependencies")
    if deps_node is None:
        return []
    result = []
    for item in deps_node:
        if _local(item.tag) != "dependency":
            continue
        dep = _parse_dependency(item, props, managed)
        if dep is not None and dep not in result:
            result.append(dep)
    return result


def _parent_package(root: ET.Element) -> MavenPackage | None:
    """Возвращает координаты родительского POM, если он задан."""
    parent = _child(root, "parent")
    if parent is None:
        return None
    names = ("groupId", "artifactId", "version")
    values = [_text(parent, name) for name in names]
    if not all(values):
        raise MavenError("В теге parent не хватает координат Maven.")
    return MavenPackage(*values)


def _merge_context(
    root: ET.Element,
    pkg: MavenPackage,
    parent: PomContext,
) -> PomContext:
    """Добавляет настройки и зависимости текущего POM к родителю."""
    props = _properties(root, pkg, parent.props)
    managed = dict(parent.managed)
    managed.update(_managed_versions(root, props))
    deps = list(parent.dependencies)
    deps.extend(_direct_dependencies(root, props, managed))
    unique = {f"{dep.group_id}:{dep.artifact_id}": dep for dep in deps}
    return PomContext(props, managed, list(unique.values()))


def parse_direct_dependencies(
    pom_text: str,
    pkg: MavenPackage,
) -> list[MavenPackage]:
    """Разбирает прямые зависимости одного POM без загрузки родителя."""
    root = _read_root(pom_text)
    props = _properties(root, pkg, {})
    managed = _managed_versions(root, props)
    return _direct_dependencies(root, props, managed)


def _load_context(repository: str, pkg: MavenPackage) -> PomContext:
    """Загружает POM и цепочку родителей от родителя к дочернему пакету."""
    chain = []
    seen = set()
    current = pkg
    while current is not None:
        if current.id in seen:
            raise MavenError(f"Обнаружен цикл родительских POM: {current.id}")
        if len(chain) >= MAX_PARENT_DEPTH:
            raise MavenError("Слишком много уровней родительских POM.")
        seen.add(current.id)
        root = _read_root(fetch_pom(repository, current))
        chain.append((current, root))
        current = _parent_package(root)
    context = PomContext({}, {}, [])
    for item, root in reversed(chain):
        context = _merge_context(root, item, context)
    return context


def _pom_url(repository: str, pkg: MavenPackage) -> str:
    """Строит адрес POM-файла в Maven-репозитории."""
    group = "/".join(urllib.parse.quote(x) for x in pkg.group_id.split("."))
    artifact = urllib.parse.quote(pkg.artifact_id)
    version = urllib.parse.quote(pkg.version, safe=".+-")
    file_name = f"{artifact}-{version}.pom"
    return f"{repository.rstrip('/')}/{group}/{artifact}/{version}/{file_name}"


def fetch_pom(repository: str, pkg: MavenPackage) -> str:
    """Загружает POM обычным HTTP-запросом из стандартной библиотеки."""
    url = _pom_url(repository, pkg)
    headers = {"User-Agent": "MireaDependencyTool/1.0"}
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        raise MavenError(f"HTTP {error.code} при загрузке {url}") from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise MavenError(f"Не удалось загрузить {url}: {error}") from error


def get_direct_dependencies(
    repository: str,
    pkg: MavenPackage,
) -> list[MavenPackage]:
    """Получает зависимости с учётом свойств и зависимостей родительских POM."""
    return _load_context(repository, pkg).dependencies
