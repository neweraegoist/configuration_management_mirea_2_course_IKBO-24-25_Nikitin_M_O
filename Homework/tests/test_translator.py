"""Tests for syntax, constants, expressions, nesting, and YAML output."""

import unittest
from pathlib import Path

import yaml

from src.errors import ConfigError
from src.translator import translate


ROOT = Path(__file__).resolve().parents[1]


class TranslatorTests(unittest.TestCase):
    """Check every language feature required by variant 16."""

    def test_hex_numbers_and_nested_dictionaries(self) -> None:
        """Hexadecimal values work inside nested dictionaries."""
        source = "dict(server = dict(port = 0x1F90))"
        result = yaml.safe_load(translate(source))
        self.assertEqual(result["server"]["port"], 8080)

    def test_multiline_comment(self) -> None:
        """Multi-line comments are ignored by the parser."""
        source = "/+ comment\nwith two lines +/ dict(value = 0xA)"
        result = yaml.safe_load(translate(source))
        self.assertEqual(result["value"], 10)

    def test_global_constant_reference(self) -> None:
        """A declared constant can be used in an expression."""
        source = "global PORT = 0x50; dict(port = {PORT})"
        result = yaml.safe_load(translate(source))
        self.assertEqual(result["port"], 80)

    def test_constant_can_use_previous_constant(self) -> None:
        """A constant expression can use an earlier constant."""
        source = (
            "global BASE = 0x10; "
            "global PORT = {BASE + 0x2}; "
            "dict(port = {PORT})"
        )
        result = yaml.safe_load(translate(source))
        self.assertEqual(result["port"], 18)

    def test_add_subtract_multiply_and_divide(self) -> None:
        """All four arithmetic operators return correct values."""
        source = (
            "global BASE = 0x10; "
            "dict(total = {BASE + 0x4}, "
            "difference = {BASE - 0x4}, "
            "product = {BASE * 0x2}, "
            "quotient = {BASE / 0x4})"
        )
        result = yaml.safe_load(translate(source))
        self.assertEqual(result["total"], 20)
        self.assertEqual(result["difference"], 12)
        self.assertEqual(result["product"], 32)
        self.assertEqual(result["quotient"], 4)

    def test_square_root_and_modulo(self) -> None:
        """The sqrt and mod functions are evaluated."""
        source = "dict(root = {sqrt(0x100)}, rest = {mod(0x17, 0x5)})"
        result = yaml.safe_load(translate(source))
        self.assertEqual(result["root"], 16)
        self.assertEqual(result["rest"], 3)

    def test_operator_precedence_and_nested_functions(self) -> None:
        """Multiplication is evaluated before addition."""
        source = "dict(value = {0x2 + 0x3 * sqrt(0x10)})"
        result = yaml.safe_load(translate(source))
        self.assertEqual(result["value"], 14)

    def test_dictionary_constant_can_be_inserted(self) -> None:
        """A dictionary constant can be inserted into another dictionary."""
        source = (
            "global LIMITS = dict(low = 0x1, high = 0xA); "
            "dict(settings = {LIMITS})"
        )
        result = yaml.safe_load(translate(source))
        self.assertEqual(result["settings"], {"low": 1, "high": 10})

    def test_duplicate_dictionary_key(self) -> None:
        """Duplicate keys are rejected."""
        with self.assertRaises(ConfigError):
            translate("dict(value = 0x1, value = 0x2)")

    def test_duplicate_constant(self) -> None:
        """Duplicate constant declarations are rejected."""
        source = "global VALUE = 0x1; global VALUE = 0x2; dict(a = 0x1)"
        with self.assertRaises(ConfigError):
            translate(source)

    def test_unknown_constant(self) -> None:
        """References to missing constants are rejected."""
        with self.assertRaises(ConfigError):
            translate("dict(value = {UNKNOWN + 0x1})")

    def test_division_by_zero(self) -> None:
        """Division by zero produces a project error."""
        with self.assertRaises(ConfigError):
            translate("dict(value = {0x5 / 0x0})")

    def test_modulo_by_zero(self) -> None:
        """Modulo by zero produces a project error."""
        with self.assertRaises(ConfigError):
            translate("dict(value = {mod(0x5, 0x0)})")

    def test_square_root_of_negative_value(self) -> None:
        """The square root of a negative value is rejected."""
        with self.assertRaises(ConfigError):
            translate("dict(value = {sqrt(0x1 - 0x2)})")

    def test_syntax_error(self) -> None:
        """Invalid source syntax is reported."""
        with self.assertRaises(ConfigError):
            translate("dict(value = 0xG1)")

    def test_all_three_domain_examples(self) -> None:
        """All domain examples are valid and produce dictionaries."""
        example_files = sorted((ROOT / "examples").glob("*.cfg"))
        self.assertEqual(len(example_files), 3)
        for path in example_files:
            with self.subTest(example=path.name):
                result = yaml.safe_load(translate(path.read_text()))
                self.assertIsInstance(result, dict)
                self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
