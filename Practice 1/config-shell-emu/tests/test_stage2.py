"""Тесты для проверки второго этапа (Скрипты)."""
import io
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from emulator import ShellEmulator

class TestStage2(unittest.TestCase):
    def test_script_stops_on_error(self):
        test_script = Path("temp_test.txt")
        test_script.write_text("ls\nfoo\ncd /\n", encoding="utf-8")

        emu = ShellEmulator(vfs_path="demo/vfs.xml", script_path=str(test_script))
        
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            emu.run()

        test_script.unlink()
        
        self.assertIn("etc/", out.getvalue())
        self.assertNotIn("cd", out.getvalue()) # cd не должен выполниться
        self.assertIn("command not found", err.getvalue())

if __name__ == "__main__":
    unittest.main()
