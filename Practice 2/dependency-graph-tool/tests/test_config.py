"""Тесты чтения и проверки XML-конфигурации."""

from pathlib import Path

import pytest

from config import ConfigError, load_config

EXAMPLES = Path(__file__).parents[1] / "examples"
FULL_DEPTH = 10
ZERO_DEPTH = 0


def test_load_valid_config() -> None:
    """Корректный тестовый XML читается без ошибок."""
    config = load_config(str(EXAMPLES / "config_test_simple.xml"))
    assert config.package_name == "A"
    assert config.test_mode
    assert config.max_depth == FULL_DEPTH


def test_relative_repository_path() -> None:
    """Путь к тестовому графу считается от папки XML."""
    config = load_config(str(EXAMPLES / "config_test_simple.xml"))
    assert Path(config.repository).name == "test_repo_simple.txt"
    assert Path(config.repository).is_file()


@pytest.mark.parametrize(
    "name",
    ["package_name", "repository", "test_mode", "version",
     "ascii_tree", "max_depth"],
)
def test_invalid_parameter_examples(name: str) -> None:
    """Каждый параметр имеет отдельный пример некорректного значения."""
    path = EXAMPLES / "errors" / f"{name}.xml"
    with pytest.raises(ConfigError):
        load_config(str(path))


def test_missing_config_file() -> None:
    """Отсутствующий XML вызывает понятную ошибку."""
    with pytest.raises(ConfigError, match="не найден"):
        load_config(str(EXAMPLES / "missing.xml"))


def test_broken_xml(tmp_path: Path) -> None:
    """Синтаксически неверный XML отклоняется."""
    path = tmp_path / "bad.xml"
    path.write_text("<config>", encoding="utf-8")
    with pytest.raises(ConfigError, match="XML"):
        load_config(str(path))


def test_missing_parameter(tmp_path: Path) -> None:
    """Отсутствующий обязательный параметр обнаруживается."""
    path = tmp_path / "missing_tag.xml"
    path.write_text("<config />", encoding="utf-8")
    with pytest.raises(ConfigError, match="package_name"):
        load_config(str(path))


def test_zero_depth_is_allowed(tmp_path: Path) -> None:
    """Нулевая глубина оставляет только корневой пакет."""
    path = tmp_path / "zero.xml"
    repo = tmp_path / "test_repo_simple.txt"
    source = EXAMPLES / "test_repo_simple.txt"
    repo.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    xml = (EXAMPLES / "config_test_simple.xml").read_text(encoding="utf-8")
    xml = xml.replace("test_repo_simple.txt", repo.name)
    xml = xml.replace("<max_depth>10", f"<max_depth>{ZERO_DEPTH}")
    path.write_text(xml, encoding="utf-8")
    config = load_config(str(path))
    assert config.max_depth == ZERO_DEPTH
