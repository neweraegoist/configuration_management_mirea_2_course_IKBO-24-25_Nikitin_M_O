from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path
from typing import Callable, Optional

from vfs import VirtualFileSystem

DEFAULT_VFS_NAME = "vfs"
EXIT_CODE_SUCCESS = 0
EXIT_CODE_MAX = 255


class CommandError(Exception):
    """Ошибка синтаксиса или выполнения команды эмулятора."""


class ShellEmulator:
    """Консольный эмулятор командной строки с виртуальной ФС."""

    def __init__(
        self,
        vfs_path: Optional[str],
        script_path: Optional[str],
    ) -> None:
        self.vfs = VirtualFileSystem()
        self.vfs_name = DEFAULT_VFS_NAME

        if vfs_path:
            self.vfs.load_from_xml(vfs_path)
            self.vfs_name = Path(vfs_path).stem

        self.script_path = script_path
        self.running = True
        self.exit_code = EXIT_CODE_SUCCESS
        self.commands: dict[str, Callable[[list[str]], None]] = {
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "exit": self.cmd_exit,
        }

    def prompt(self) -> str:
        return f"{self.vfs_name}:{self.vfs.cwd.name}$ "

    def _read_line(self) -> str:
        if sys.stdin.isatty():
            return input(self.prompt())

        sys.stdout.write(self.prompt())
        sys.stdout.flush()
        raw_line = sys.stdin.readline()
        if not raw_line:
            raise EOFError

        sys.stdout.write(raw_line)
        sys.stdout.flush()
        return raw_line.rstrip("\r\n")

    def parse(self, line: str) -> tuple[Optional[str], list[str]]:
        try:
            tokens = shlex.split(line, posix=True)
        except ValueError as exc:
            raise CommandError(f"syntax error: {exc}") from exc

        if not tokens:
            return None, []
        return tokens[0], tokens[1:]

    def execute(self, line: str) -> bool:
        try:
            command, args = self.parse(line)
        except CommandError as exc:
            print(f"{self.vfs_name}: {exc}", file=sys.stderr)
            return False

        if command is None:
            return True

        handler = self.commands.get(command)
        if handler is None:
            print(
                f"{self.vfs_name}: {command}: command not found",
                file=sys.stderr,
            )
            return False

        try:
            handler(args)
        except CommandError as exc:
            print(f"{self.vfs_name}: {command}: {exc}", file=sys.stderr)
            return False

        return True

    def cmd_ls(self, args: list[str]) -> None:
        if len(args) > 1:
            raise CommandError("too many arguments")

        path = args[0] if args else "."
        node = self.vfs.get_node(path)
        if node is None:
            raise CommandError(
                f"cannot access '{path}': No such file or directory"
            )

        if not node.is_dir:
            print(node.name)
            return

        items = sorted(
            node.children.values(),
            key=lambda item: (not item.is_dir, item.name),
        )
        for item in items:
            suffix = "/" if item.is_dir else ""
            print(f"{item.name}{suffix}")

    def cmd_cd(self, args: list[str]) -> None:
        if len(args) > 1:
            raise CommandError("too many arguments")

        path = args[0] if args else "/"
        node = self.vfs.get_node(path)
        if node is None:
            raise CommandError(f"no such file or directory: {path}")
        if not node.is_dir:
            raise CommandError(f"not a directory: {path}")

        self.vfs.cwd = node

    def cmd_exit(self, args: list[str]) -> None:
        if len(args) > 1:
            raise CommandError("too many arguments")

        code = EXIT_CODE_SUCCESS
        if args:
            try:
                code = int(args[0])
            except ValueError as exc:
                raise CommandError(
                    f"invalid exit code: {args[0]!r}"
                ) from exc

        if not EXIT_CODE_SUCCESS <= code <= EXIT_CODE_MAX:
            raise CommandError(f"exit code out of range: {code}")

        self.exit_code = code
        self.running = False

    def run_script(self) -> None:
        if not self.script_path:
            return

        try:
            with open(self.script_path, "r", encoding="utf-8") as file:
                for raw_line in file:
                    line = raw_line.rstrip("\r\n")
                    if not line.strip():
                        continue

                    print(f"{self.prompt()}{line}")
                    if not self.execute(line):
                        print(
                            "[ОШИБКА] Выполнение скрипта прервано.",
                            file=sys.stderr,
                        )
                        self.exit_code = 1
                        break

                    if not self.running:
                        break
        except OSError as exc:
            print(
                f"Ошибка чтения стартового скрипта: {exc}",
                file=sys.stderr,
            )
            self.exit_code = 1
        finally:
            self.running = False

    def run(self) -> int:
        if self.script_path:
            self.run_script()
            return self.exit_code

        while self.running:
            try:
                line = self._read_line()
            except EOFError:
                print()
                break
            except KeyboardInterrupt:
                print()
                continue

            self.execute(line)

        return self.exit_code


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Эмулятор командной строки, вариант №16"
    )
    parser.add_argument(
        "--vfs",
        default=None,
        help="Путь к XML-файлу виртуальной файловой системы",
    )
    parser.add_argument(
        "--script",
        default=None,
        help="Путь к стартовому скрипту команд эмулятора",
    )
    args = parser.parse_args()

    print("[DEBUG] Параметры запуска эмулятора:")
    print(f"[DEBUG] VFS: {args.vfs}")
    print(f"[DEBUG] Script: {args.script}")
    print("-" * 30)

    try:
        emulator = ShellEmulator(args.vfs, args.script)
    except ValueError as exc:
        print(f"[ОШИБКА VFS] {exc}", file=sys.stderr)
        return 1

    return emulator.run()

if __name__ == "__main__":
    sys.exit(main())
