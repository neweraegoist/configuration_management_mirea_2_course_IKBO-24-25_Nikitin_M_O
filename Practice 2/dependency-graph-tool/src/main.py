"""CLI-приложение для всех пяти этапов варианта №16."""

from __future__ import annotations

import argparse
import sys

from compare_maven import compare_with_maven
from config import Config, ConfigError, load_config
from graph import GraphCycleError, build_graph, compute_load_order
from maven import MavenError, MavenPackage, get_direct_dependencies
from testrepo import RepositoryFormatError, load_graph
from visualize import to_ascii_tree, to_plantuml

EXIT_SUCCESS = 0
EXIT_ERROR = 1
STAGE_CONFIG = 1
STAGE_DIRECT = 2
STAGE_GRAPH = 3
STAGE_ORDER = 4
STAGE_VISUAL = 5
STAGES = (STAGE_CONFIG, STAGE_DIRECT, STAGE_GRAPH, STAGE_ORDER,
          STAGE_VISUAL)


def make_resolver(config: Config):
    """Выбирает источник зависимостей: тестовый файл или Maven."""
    if config.test_mode:
        data = load_graph(config.repository)
        root = config.package_name
        if root not in data:
            raise RepositoryFormatError(f"Пакет {root} отсутствует в файле.")
        return root, lambda node: data.get(node, [])
    root_pkg = MavenPackage(
        config.package_name.split(":")[0],
        config.package_name.split(":")[1],
        config.version,
    )

    def get_deps(node: str) -> list[str]:
        """Возвращает прямые зависимости одного Maven-пакета."""
        package = MavenPackage.parse(node)
        deps = get_direct_dependencies(config.repository, package)
        return [item.id for item in deps]

    return root_pkg.id, get_deps


def _print_direct(root: str, get_deps) -> None:
    """Выводит прямые зависимости корневого пакета."""
    print(f"\nПрямые зависимости {root}:")
    for dep in get_deps(root):
        print(f"- {dep}")


def _print_graph(
    graph: dict[str, list[str]], cycles: list[tuple[str, str]]
) -> None:
    """Показывает список рёбер и обнаруженные циклы."""
    print("\nГраф зависимостей:")
    for node, deps in graph.items():
        print(f"{node} -> {', '.join(deps) if deps else 'нет'}")
    if cycles:
        print("\nЦиклические рёбра:")
        for first, second in cycles:
            print(f"{first} -> {second}")


def _print_order(order: list[str]) -> None:
    """Выводит зависимости в порядке загрузки."""
    print("\nПорядок загрузки (сначала зависимости):")
    for number, node in enumerate(order, 1):
        print(f"{number}. {node}")


def _compare(root: str, config: Config, order: list[str]) -> None:
    """Сравнивает граф с реальным выводом Maven CLI."""
    if config.test_mode:
        raise MavenError(
            "Сравнение с Maven доступно только в реальном режиме.")
    package = MavenPackage.parse(root)
    result, only_ours, only_maven = compare_with_maven(
        package, config.repository, order)
    print("\nЗависимости по Maven dependency:tree:")
    for item in result:
        print(f"- {item}")
    print(f"Есть только в нашей программе: {only_ours or 'нет'}")
    print(f"Есть только в Maven: {only_maven or 'нет'}")
    print("Maven показывает дерево сверху вниз, наш список — снизу вверх.")


def _run_stage(
    stage: int,
    root: str,
    get_deps,
    config: Config,
    compare: bool,
) -> int:
    """Выполняет выбранный этап после чтения конфигурации."""
    if stage == STAGE_CONFIG:
        return EXIT_SUCCESS
    if stage == STAGE_DIRECT:
        _print_direct(root, get_deps)
        return EXIT_SUCCESS
    graph, cycles = build_graph(root, get_deps, config.max_depth)
    if stage == STAGE_GRAPH:
        _print_graph(graph, cycles)
        return EXIT_SUCCESS
    if stage == STAGE_ORDER:
        if cycles:
            raise GraphCycleError(
                "Порядок загрузки невозможен: в графе есть цикл."
            )
        order = compute_load_order(graph, root)
        _print_order(order)
        if compare:
            _compare(root, config, order)
        return EXIT_SUCCESS
    print("\nОписание графа PlantUML:\n")
    print(to_plantuml(graph))
    if config.ascii_tree:
        print("\nASCII-дерево:\n")
        print(to_ascii_tree(graph, root))
    return EXIT_SUCCESS


def run(config_path: str, stage: int, compare: bool = False) -> int:
    """Запускает программу и показывает понятные сообщения об ошибках."""
    try:
        config = load_config(config_path)
        if stage == STAGE_CONFIG:
            config.print_params()
            return EXIT_SUCCESS
        root, get_deps = make_resolver(config)
        return _run_stage(stage, root, get_deps, config, compare)
    except (ConfigError, MavenError, RepositoryFormatError,
            GraphCycleError, OSError, ValueError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR


def main() -> int:
    """Разбирает аргументы командной строки."""
    parser = argparse.ArgumentParser(
        description="Визуализатор графа зависимостей Maven, вариант 16.")
    parser.add_argument("config", help="путь к XML-файлу конфигурации")
    parser.add_argument("--stage", type=int, choices=STAGES, default=5)
    parser.add_argument(
        "--compare-maven", action="store_true",
        help="сравнить порядок с Maven CLI на этапе 4")
    args = parser.parse_args()
    if args.compare_maven and args.stage != STAGE_ORDER:
        parser.error("--compare-maven можно использовать только с --stage 4")
    return run(args.config, args.stage, args.compare_maven)


if __name__ == "__main__":
    raise SystemExit(main())
