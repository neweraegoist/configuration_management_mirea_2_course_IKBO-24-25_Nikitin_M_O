import io
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from emulator import CommandError, ShellEmulator  # noqa: E402


class TestParser(unittest.TestCase):

    def setUp(self):
        self.emulator = ShellEmulator(None, None)

    def test_simple_command(self):
        self.assertEqual(
            self.emulator.parse("ls -la"),
            ("ls", ["-la"]),
        )

    def test_double_quoted_argument(self):
        self.assertEqual(
            self.emulator.parse('ls "my folder"'),
            ("ls", ["my folder"]),
        )

    def test_single_quoted_argument(self):
        self.assertEqual(
            self.emulator.parse("ls 'my folder'"),
            ("ls", ["my folder"]),
        )

    def test_unterminated_quote(self):
        with self.assertRaises(CommandError):
            self.emulator.parse('ls "broken')


class TestCommandErrors(unittest.TestCase):

    def setUp(self):
        self.emulator = ShellEmulator(None, None)

    def test_unknown_command(self):
        errors = io.StringIO()
        with redirect_stderr(errors):
            success = self.emulator.execute("unknown argument")

        self.assertFalse(success)
        self.assertIn("command not found", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
