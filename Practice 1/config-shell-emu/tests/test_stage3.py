import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from emulator import ShellEmulator  # noqa: E402
from vfs import VirtualFileSystem  # noqa: E402

VFS_FILE = PROJECT_DIR / "demo" / "vfs.xml"


class TestVFSCommands(unittest.TestCase):

    def setUp(self):
        self.emulator = ShellEmulator(str(VFS_FILE), None)

    def run_command(self, command):
        output = io.StringIO()
        errors = io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            success = self.emulator.execute(command)
        return success, output.getvalue(), errors.getvalue()

    def test_ls_root(self):
        success, output, _ = self.run_command("ls")
        self.assertTrue(success)
        self.assertIn("home/", output)
        self.assertIn("etc/", output)
        self.assertIn("root_file.txt", output)

    def test_cd_and_ls_nested_directory(self):
        self.assertTrue(self.run_command("cd home")[0])
        self.assertTrue(self.run_command("cd user")[0])
        success, output, _ = self.run_command("ls")
        self.assertTrue(success)
        self.assertIn("documents/", output)
        self.assertIn("profile.json", output)

    def test_cd_parent_directory(self):
        self.run_command("cd home/user")
        self.assertTrue(self.run_command("cd ..")[0])
        success, output, _ = self.run_command("ls")
        self.assertTrue(success)
        self.assertIn("user/", output)

    def test_cd_missing_path(self):
        success, _, errors = self.run_command("cd missing")
        self.assertFalse(success)
        self.assertIn("no such file or directory", errors)

    def test_cd_to_file(self):
        success, _, errors = self.run_command("cd root_file.txt")
        self.assertFalse(success)
        self.assertIn("not a directory", errors)

    def test_ls_rejects_extra_arguments(self):
        success, _, errors = self.run_command("ls one two")
        self.assertFalse(success)
        self.assertIn("too many arguments", errors)


class TestXMLValidation(unittest.TestCase):

    def load_temporary_xml(self, xml_text):
        temporary_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_dir.cleanup)
        xml_path = Path(temporary_dir.name) / "test_vfs.xml"
        xml_path.write_text(xml_text, encoding="utf-8")
        VirtualFileSystem().load_from_xml(str(xml_path))

    def test_wrong_root_element(self):
        with self.assertRaisesRegex(ValueError, "<vfs>"):
            self.load_temporary_xml("<filesystem />")

    def test_unknown_element(self):
        with self.assertRaisesRegex(ValueError, "Недопустимый"):
            self.load_temporary_xml("<vfs><folder name='home' /></vfs>")

    def test_missing_name(self):
        with self.assertRaisesRegex(ValueError, "name"):
            self.load_temporary_xml("<vfs><dir /></vfs>")

    def test_duplicate_names(self):
        xml_text = (
            "<vfs><file name='same.txt' />"
            "<dir name='same.txt' /></vfs>"
        )
        with self.assertRaisesRegex(ValueError, "Повторяющееся"):
            self.load_temporary_xml(xml_text)

    def test_malformed_xml(self):
        with self.assertRaisesRegex(ValueError, "Неверный формат XML"):
            self.load_temporary_xml("<vfs><dir></vfs>")


if __name__ == "__main__":
    unittest.main()
