"""Тесты этапа 2: параметры запуска и стартовый скрипт."""

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from emulator import ShellEmulator  # noqa: E402

VFS_FILE = PROJECT_DIR / "demo" / "vfs.xml"


class TestStage2(unittest.TestCase):
    """Проверяет запуск стартового скрипта."""

    def test_script_stops_on_first_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = Path(temp_dir) / "test_script.txt"
            script_path.write_text(
                "ls\nunknown_command\ncd /\n",
                encoding="utf-8",
            )
            emulator = ShellEmulator(str(VFS_FILE), str(script_path))
            output = io.StringIO()
            errors = io.StringIO()

            with redirect_stdout(output), redirect_stderr(errors):
                result = emulator.run()

        self.assertEqual(result, 1)
        self.assertIn("home/", output.getvalue())
        self.assertNotIn("cd /", output.getvalue())
        self.assertIn("command not found", errors.getvalue())

    def test_exit_stops_script_without_running_next_line(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = Path(temp_dir) / "exit_script.txt"
            script_path.write_text(
                "exit\nunknown_command\n",
                encoding="utf-8",
            )
            emulator = ShellEmulator(str(VFS_FILE), str(script_path))
            output = io.StringIO()
            errors = io.StringIO()

            with redirect_stdout(output), redirect_stderr(errors):
                result = emulator.run()

        self.assertEqual(result, 0)
        self.assertIn("exit", output.getvalue())
        self.assertNotIn("unknown_command", output.getvalue())
        self.assertEqual(errors.getvalue(), "")

    def test_missing_script_returns_error(self):
        emulator = ShellEmulator(
            str(VFS_FILE),
            str(PROJECT_DIR / "demo" / "missing_script.txt"),
        )
        errors = io.StringIO()

        with redirect_stderr(errors):
            result = emulator.run()

        self.assertEqual(result, 1)
        self.assertIn("Ошибка чтения", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
