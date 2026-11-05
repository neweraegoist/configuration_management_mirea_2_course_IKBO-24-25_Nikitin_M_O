"""Тесты для проверки третьего этапа (VFS)."""
import io
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from emulator import ShellEmulator

class TestVFS(unittest.TestCase):
    def setUp(self):
        # Используем тестовый XML файл
        self.emu = ShellEmulator(vfs_path="demo/vfs.xml", script_path=None)

    def _run(self, line):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            self.emu.execute(line)
        return out.getvalue(), err.getvalue()

    def test_ls_root(self):
        out, _ = self._run("ls")
        self.assertIn("home/", out)
        self.assertIn("etc/", out)
        self.assertIn("root_file.txt", out)

    def test_cd_and_ls(self):
        self._run("cd home")
        out, _ = self._run("ls")
        self.assertIn("user/", out)
        self.assertIn("welcome.txt", out)

    def test_cd_error(self):
        _, err = self._run("cd non_existent_folder")
        self.assertIn("no such file or directory", err)

    def test_cd_to_file_error(self):
        _, err = self._run("cd root_file.txt")
        self.assertIn("not a directory", err)

if __name__ == "__main__":
    unittest.main()
