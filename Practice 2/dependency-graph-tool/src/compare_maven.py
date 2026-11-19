"""Сравнение результата программы с выводом установленного Maven CLI."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from maven import MavenError, MavenPackage


SUCCESS_CODE = 0

_TREE_LINE = re.compile(
    r"([A-Za-z0-9_.-]+):([A-Za-z0-9_.-]+):[^:\s]+:([^:\s]+):"
    r"(?:compile|runtime|provided|test|system)\s*$"
)


def parse_maven_tree(output: str) -> list[str]:
    """Извлекает координаты артефактов из `mvn dependency:tree`."""
    result = []
    for line in output.splitlines():
        match = _TREE_LINE.search(line.strip())
        if match:
            item = ":".join(match.groups())
            if item not in result:
                result.append(item)
    return result


def _pom_text(pkg: MavenPackage, repository: str) -> str:
    """Создаёт временный POM только для сравнительного запуска Maven."""
    return (
        "<project xmlns=\"http://maven.apache.org/POM/4.0.0\">"
        "<modelVersion>4.0.0</modelVersion>"
        "<groupId>mirea.check</groupId><artifactId>compare</artifactId>"
        "<version>1.0</version><repositories><repository>"
        "<id>compare-repo</id><url>" + repository + "</url>"
        "</repository></repositories><dependencies><dependency>"
        f"<groupId>{pkg.group_id}</groupId>"
        f"<artifactId>{pkg.artifact_id}</artifactId>"
        f"<version>{pkg.version}</version>"
        "</dependency></dependencies></project>"
    )


def compare_with_maven(
    pkg: MavenPackage,
    repository: str,
    our_order: list[str],
) -> tuple[list[str], list[str], list[str]]:
    """Сравнивает найденные координаты с Maven dependency:tree."""
    # Maven запускается только для сравнения, а не для сбора данных.
    command = shutil.which("mvn")
    if command is None:
        raise MavenError("Команда mvn не найдена. Установите Apache Maven.")
    with tempfile.TemporaryDirectory() as folder:
        pom = Path(folder) / "pom.xml"
        pom.write_text(_pom_text(pkg, repository), encoding="utf-8")
        args = [command, "-f", str(pom), "dependency:tree"]
        try:
            run = subprocess.run(
                args, capture_output=True, text=True, timeout=180)
        except subprocess.TimeoutExpired as error:
            raise MavenError("Maven не завершился за 180 секунд.") from error
    if run.returncode != SUCCESS_CODE:
        details = (run.stderr or run.stdout).strip()[-800:]
        raise MavenError(f"Maven завершился с ошибкой: {details}")
    maven_order = parse_maven_tree(run.stdout + run.stderr)
    our_set = set(our_order) - {pkg.id}
    maven_deps = maven_order[1:] if maven_order else []
    maven_set = set(maven_deps)
    only_ours = sorted(our_set - maven_set)
    only_maven = sorted(maven_set - our_set)
    return maven_order, only_ours, only_maven
