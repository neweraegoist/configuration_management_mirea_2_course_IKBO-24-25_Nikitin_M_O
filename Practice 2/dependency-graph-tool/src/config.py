"""Чтение и проверка XML-конфигурации."""

from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from urllib.parse import urlsplit


ONE_REQUIRED_VALUE = 1


class ConfigError(Exception):
    """Понятная ошибка пользовательской конфигурации."""


@dataclass(frozen=True)
class Config:
    """Шесть параметров, заданных в XML-файле."""

    package_name: str
    repository: str
    test_mode: bool
    version: str
    ascii_tree: bool
    max_depth: int

    def print_params(self) -> None:
        """Печатает настройки в формате ключ=значение."""
        for key, value in self.__dict__.items():
            print(f"{key}={value}")


def _tag_text(root: ET.Element, name: str) -> str:
    """Возвращает непустое значение обязательного XML-тега."""
    nodes = root.findall(name)
    if len(nodes) != ONE_REQUIRED_VALUE or nodes[0].text is None:
        raise ConfigError(f"Параметр <{name}> должен быть указан один раз.")
    value = nodes[0].text.strip()
    if not value:
        raise ConfigError(f"Параметр <{name}> не может быть пустым.")
    return value


def _boolean(name: str, value: str) -> bool:
    """Преобразует строку XML в логическое значение."""
    values = {"true": True, "false": False}
    if value.lower() not in values:
        raise ConfigError(f"Параметр <{name}> должен быть true или false.")
    return values[value.lower()]


def _depth(value: str) -> int:
    """Проверяет и возвращает неотрицательную глубину графа."""
    if not value.isdigit():
        raise ConfigError("Параметр <max_depth> должен быть целым числом >= 0.")
    return int(value)


def _valid_package(value: str, test_mode: bool) -> bool:
    """Проверяет имя тестового или Maven-пакета."""
    if test_mode:
        return re.fullmatch(r"[A-Z]+", value) is not None
    pattern = r"[A-Za-z0-9_.-]+:[A-Za-z0-9_.-]+"
    return re.fullmatch(pattern, value) is not None


def _valid_url(value: str) -> bool:
    """Проверяет HTTP(S)-адрес Maven-репозитория."""
    try:
        parsed = urlsplit(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except ValueError:
        return False


def _repository_path(value: str, config_path: str) -> str:
    """Разрешает относительный путь относительно XML-файла."""
    if os.path.isabs(value):
        return value
    folder = os.path.dirname(os.path.abspath(config_path))
    return os.path.normpath(os.path.join(folder, value))


def _read_root(path: str) -> ET.Element:
    """Открывает XML и проверяет его корневой элемент."""
    if not os.path.isfile(path):
        raise ConfigError(f"Файл конфигурации не найден: {path}")
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as error:
        raise ConfigError(f"Не удалось прочитать XML: {error}") from error
    if root.tag != "config":
        raise ConfigError("Корневой XML-тег должен называться <config>.")
    return root


def _check_package(value: str, test_mode: bool) -> None:
    """Проверяет формат имени пакета."""
    if _valid_package(value, test_mode):
        return
    expected = (
        "заглавные латинские буквы" if test_mode else "groupId:artifactId"
    )
    raise ConfigError(f"<package_name> должен иметь формат {expected}.")


def _check_repository(value: str, path: str, test_mode: bool) -> str:
    """Проверяет URL или возвращает путь к тестовому файлу."""
    if not test_mode:
        if not _valid_url(value):
            raise ConfigError(
                "<repository> должен быть полным HTTP(S)-адресом.")
        return value
    result = _repository_path(value, path)
    if not os.path.isfile(result):
        raise ConfigError(
            f"Файл тестового репозитория не найден: {result}")
    return result


def _make_config(values: dict[str, str], path: str) -> Config:
    """Проверяет значения и создаёт объект настроек."""
    test_mode = _boolean("test_mode", values["test_mode"])
    package = values["package_name"]
    _check_package(package, test_mode)
    repository = _check_repository(
        values["repository"], path, test_mode)
    version = values["version"]
    version_pattern = r"[A-Za-z0-9][A-Za-z0-9._+-]*"
    if re.fullmatch(version_pattern, version) is None:
        raise ConfigError("<version> содержит недопустимые символы.")
    ascii_tree = _boolean("ascii_tree", values["ascii_tree"])
    max_depth = _depth(values["max_depth"])
    return Config(package, repository, test_mode, version, ascii_tree,
                  max_depth)


def load_config(path: str) -> Config:
    """Загружает XML и проверяет все шесть параметров."""
    root = _read_root(path)
    names = ("package_name", "repository", "test_mode", "version",
             "ascii_tree", "max_depth")
    if any(child.tag not in names for child in root):
        raise ConfigError("В XML есть неизвестный параметр.")
    values = {name: _tag_text(root, name) for name in names}
    return _make_config(values, path)
