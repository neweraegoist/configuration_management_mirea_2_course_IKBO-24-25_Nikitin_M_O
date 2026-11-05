"""Тесты для проверки первого этапа (REPL)."""
import io
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from emulator import ShellEmulator, CommandError

class TestParser(unittest.TestCase):
    def setUp(self):
        self.emu = ShellEmulator(vfs_path=None, script_path=None)

    def test_simple(self):
        self.assertEqual(self.emu.parse("ls -la"), ("ls", ["-la"]))

    def test_quoted(self):
        self.assertEqual(self.emu.parse('ls "my file"'), ("ls", ["my file"]))

    def test_unterminated(self):
        with self.assertRaises(CommandError):
            self.emu.parse('ls "abc')

class TestCommands(unittest.TestCase):
    def setUp(self):
        self.emu = ShellEmulator(vfs_path=None, script_path=None)

    def _run(self, line):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            self.emu.execute(line)
        return out.getvalue(), err.getvalue()

    def test_unknown_command(self):
        _, err = self._run("foo bar")
        self.assertIn("command not found", err)

if __name__ == "__main__":
    unittest.main()
