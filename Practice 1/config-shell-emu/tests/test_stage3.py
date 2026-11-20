"""Проверка команд VFS и ошибок XML."""

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

from emulator import ShellEmulator
from vfs import VirtualFileSystem

VFS_FILE = PROJECT_DIR / "demo" / "vfs.xml"


class TestVFSCommands(unittest.TestCase):
    """Проверяет навигацию и просмотр виртуальных каталогов."""

    def setUp(self):
        """Создаёт отдельный экземпляр эмулятора для каждого теста."""
        self.emulator = ShellEmulator(str(VFS_FILE), None)

    def run_command(self, command):
        """Выполняет команду с перехватом стандартного вывода и ошибок."""
        output = io.StringIO()
        errors = io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            success = self.emulator.execute(command)
        return success, output.getvalue(), errors.getvalue()

    def test_ls_root(self):
        """Выводит файлы и каталоги корневого узла."""
        success, output, _ = self.run_command("ls")
        self.assertTrue(success)
        self.assertIn("home/", output)
        self.assertIn("etc/", output)
        self.assertIn("root_file.txt", output)

    def test_cd_and_ls_nested_directory(self):
        """Переходит во вложенный каталог и выводит его содержимое."""
        self.assertTrue(self.run_command("cd home")[0])
        self.assertTrue(self.run_command("cd user")[0])
        success, output, _ = self.run_command("ls")
        self.assertTrue(success)
        self.assertIn("documents/", output)
        self.assertIn("profile.json", output)

    def test_cd_parent_directory(self):
        """Переходит из вложенного каталога к родителю."""
        self.run_command("cd home/user")
        self.assertTrue(self.run_command("cd ..")[0])
        success, output, _ = self.run_command("ls")
        self.assertTrue(success)
        self.assertIn("user/", output)

    def test_cd_missing_path(self):
        """Сообщает об ошибке перехода по отсутствующему пути."""
        success, _, errors = self.run_command("cd missing")
        self.assertFalse(success)
        self.assertIn("no such file or directory", errors)

    def test_cd_to_file(self):
        """Отклоняет попытку перейти в файл вместо каталога."""
        success, _, errors = self.run_command("cd root_file.txt")
        self.assertFalse(success)
        self.assertIn("not a directory", errors)

    def test_ls_rejects_extra_arguments(self):
        """Отклоняет лишние аргументы команды ls."""
        success, _, errors = self.run_command("ls one two")
        self.assertFalse(success)
        self.assertIn("too many arguments", errors)

    def test_file_cannot_be_used_as_directory(self):
        """Отклоняет продолжение пути после обычного файла."""
        paths = ("root_file.txt/", "root_file.txt/.", "root_file.txt/..")
        for path in paths:
            with self.subTest(path=path):
                self.assertIsNone(self.emulator.vfs.get_node(path))

    def test_directory_accepts_slash_and_current_component(self):
        """Сохраняет навигацию по каталогам после проверки типов узлов."""
        directory = self.emulator.vfs.get_node("home")
        self.assertIs(self.emulator.vfs.get_node("home/"), directory)
        self.assertIs(self.emulator.vfs.get_node("home/."), directory)
        self.assertIs(
            self.emulator.vfs.get_node("/.."), self.emulator.vfs.root)


class TestXMLValidation(unittest.TestCase):
    """Проверяет отклонение некорректной структуры XML."""

    def load_temporary_xml(self, xml_text):
        """Загружает временный XML с автоматическим удалением файла."""
        temporary_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_dir.cleanup)
        xml_path = Path(temporary_dir.name) / "test_vfs.xml"
        xml_path.write_text(xml_text, encoding="utf-8")
        VirtualFileSystem().load_from_xml(str(xml_path))

    def test_wrong_root_element(self):
        """Отклоняет XML с неверным корневым элементом."""
        with self.assertRaisesRegex(ValueError, "<vfs>"):
            self.load_temporary_xml("<filesystem />")

    def test_unknown_element(self):
        """Отклоняет неизвестный тип узла в XML."""
        with self.assertRaisesRegex(ValueError, "Недопустимый"):
            self.load_temporary_xml("<vfs><folder name='home' /></vfs>")

    def test_missing_name(self):
        """Отклоняет XML-узел без обязательного имени."""
        with self.assertRaisesRegex(ValueError, "name"):
            self.load_temporary_xml("<vfs><dir /></vfs>")

    def test_duplicate_names(self):
        """Отклоняет повторяющиеся имена в одном каталоге."""
        xml_text = (
            "<vfs><file name='same.txt' />"
            "<dir name='same.txt' /></vfs>"
        )
        with self.assertRaisesRegex(ValueError, "Повторяющееся"):
            self.load_temporary_xml(xml_text)

    def test_malformed_xml(self):
        """Отклоняет синтаксически неверный XML."""
        with self.assertRaisesRegex(ValueError, "Неверный формат XML"):
            self.load_temporary_xml("<vfs><dir></vfs>")


if __name__ == "__main__":
    unittest.main()
