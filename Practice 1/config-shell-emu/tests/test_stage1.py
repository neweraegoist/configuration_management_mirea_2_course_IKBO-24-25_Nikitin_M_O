"""Проверка разбора команд и обработки неизвестных команд."""

import io
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from emulator import CommandError, ShellEmulator


class TestParser(unittest.TestCase):
    """Проверяет разбор команд и аргументов в кавычках."""

    def setUp(self):
        """Создаёт отдельный экземпляр эмулятора для каждого теста."""
        self.emulator = ShellEmulator(None, None)

    def test_simple_command(self):
        """Проверяет выделение имени команды и аргумента."""
        self.assertEqual(
            self.emulator.parse("ls -la"),
            ("ls", ["-la"]),
        )

    def test_double_quoted_argument(self):
        """Сохраняет пробелы в двойных кавычках."""
        self.assertEqual(
            self.emulator.parse('ls "my folder"'),
            ("ls", ["my folder"]),
        )

    def test_single_quoted_argument(self):
        """Сохраняет пробелы в одинарных кавычках."""
        self.assertEqual(
            self.emulator.parse("ls 'my folder'"),
            ("ls", ["my folder"]),
        )

    def test_unterminated_quote(self):
        """Отклоняет аргумент с незакрытой кавычкой."""
        with self.assertRaises(CommandError):
            self.emulator.parse('ls "broken')


class TestCommandErrors(unittest.TestCase):
    """Проверяет сообщения об ошибках выполнения команд."""

    def setUp(self):
        """Создаёт отдельный экземпляр эмулятора для каждого теста."""
        self.emulator = ShellEmulator(None, None)

    def test_unknown_command(self):
        """Сообщает об ошибке неизвестной команды."""
        errors = io.StringIO()
        with redirect_stderr(errors):
            success = self.emulator.execute("unknown argument")

        self.assertFalse(success)
        self.assertIn("command not found", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
