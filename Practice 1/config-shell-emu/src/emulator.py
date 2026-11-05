"""Эмулятор оболочки. Этап 3: Виртуальная файловая система (VFS)."""
from __future__ import annotations
import argparse
import shlex
import sys
from vfs import VirtualFileSystem

DEFAULT_VFS_NAME = "vfs"
EXIT_CODE_SUCCESS = 0
EXIT_CODE_MAX = 255

class CommandError(Exception):
    """Ошибка выполнения команды."""

class ShellEmulator:
    """Класс эмулятора командной оболочки."""

    def __init__(self, vfs_path: str | None, script_path: str | None) -> None:
        self.vfs = VirtualFileSystem()
        self.vfs_name = DEFAULT_VFS_NAME
        
        # Загружаем VFS, если передан путь
        if vfs_path and vfs_path != DEFAULT_VFS_NAME:
            try:
                self.vfs.load_from_xml(vfs_path)
                self.vfs_name = vfs_path.split("/")[-1].replace(".xml", "")
            except ValueError as exc:
                print(f"[ОШИБКА VFS] {exc}", file=sys.stderr)
                sys.exit(1)

        self.script_path = script_path
        self.running = True
        self.exit_code = 0
        self.commands = {
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "exit": self.cmd_exit,
        }

    def prompt(self) -> str:
        """Формирует приглашение к вводу."""
        return f"{self.vfs_name}:{self.vfs.cwd.name}$ "

    def _read_line(self) -> str:
        """Читает строку от пользователя."""
        if sys.stdin.isatty():
            return input(self.prompt())
        sys.stdout.write(self.prompt())
        sys.stdout.flush()
        raw = sys.stdin.readline()
        if not raw:
            raise EOFError
        sys.stdout.write(raw)
        sys.stdout.flush()
        return raw.rstrip("\n")

    def parse(self, line: str):
        """Разбирает строку на команду и аргументы."""
        try:
            tokens = shlex.split(line, posix=True)
        except ValueError as exc:
            raise CommandError(f"syntax error: {exc}") from exc        
        if not tokens:
            return None, []
        return tokens[0], tokens[1:]

    def execute(self, line: str) -> bool:
        """Выполняет команду. Возвращает True, если успешно."""
        try:
            cmd, args = self.parse(line)
        except CommandError as exc:
            print(f"{self.vfs_name}: {exc}", file=sys.stderr)
            return False
            
        if cmd is None:
            return True
            
        handler = self.commands.get(cmd)
        if handler is None:
            print(f"{self.vfs_name}: {cmd}: command not found", file=sys.stderr)
            return False
            
        try:
            handler(args)
            return True
        except CommandError as exc:
            print(f"{self.vfs_name}: {cmd}: {exc}", file=sys.stderr)
            return False

    def cmd_ls(self, args):
        """Реальная команда ls — выводит содержимое папки VFS."""
        path = args[0] if args else "."
        node = self.vfs.get_node(path)
        
        if node is None:
            raise CommandError(f"cannot access '{path}': No such file or directory")
        if not node.is_dir:
            print(node.name)
            return
            
        # Сортируем для красоты: сначала папки, потом файлы
        items = sorted(node.children.values(), key=lambda x: (not x.is_dir, x.name))
        if not items:
            return
            
        for item in items:
            suffix = "/" if item.is_dir else ""
            print(f"{item.name}{suffix}")

    def cmd_cd(self, args):
        """Реальная команда cd — переходит по папкам VFS."""
        if len(args) > 1:
            raise CommandError("too many arguments")
        
        path = args[0] if args else "/"
        node = self.vfs.get_node(path)
        
        if node is None:
            raise CommandError(f"no such file or directory: {path}")
        if not node.is_dir:
            raise CommandError(f"not a directory: {path}")
            
        self.vfs.cwd = node

    def cmd_exit(self, args):
        """Команда выхода из эмулятора."""
        if len(args) > 1:
            raise CommandError("too many arguments")
        
        code = EXIT_CODE_SUCCESS
        if args:
            try:
                code = int(args[0])
            except ValueError as exc:
                raise CommandError(f"invalid exit code: {args[0]!r}") from exc
            if not EXIT_CODE_SUCCESS <= code <= EXIT_CODE_MAX:
                raise CommandError(f"exit code out of range: {code}")
        self.exit_code = code
        self.running = False

    def run_script(self) -> None:
        """Выполняет стартовый скрипт с остановкой на первой ошибке."""
        try:
            with open(self.script_path, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    
                    print(f"{self.prompt()}{line}")
                    success = self.execute(line)
                    if not success:
                        print(f"[ОШИБКА] Выполнение скрипта прервано.", file=sys.stderr)
                        self.exit_code = 1
                        break
        except FileNotFoundError:
            print(f"Ошибка: файл скрипта '{self.script_path}' не найден.", file=sys.stderr)
            self.exit_code = 1
        self.running = False

    def run(self) -> int:
        """Запускает эмулятор."""
        if self.script_path:
            self.run_script()
        else:
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
    """Точка входа. Разбирает аргументы командной строки."""
    parser = argparse.ArgumentParser(description="Эмулятор командной строки")
    parser.add_argument("--vfs", default=DEFAULT_VFS_NAME, help="Путь к VFS (XML)")
    parser.add_argument("--script", default=None, help="Путь к стартовому скрипту")
    
    args = parser.parse_args()

    print("[DEBUG] Параметры запуска эмулятора:")
    print(f"[DEBUG] VFS: {args.vfs}")
    print(f"[DEBUG] Script: {args.script}")
    print("-" * 30)

    emulator = ShellEmulator(vfs_path=args.vfs, script_path=args.script)
    return emulator.run()

if __name__ == "__main__":
    sys.exit(main())
