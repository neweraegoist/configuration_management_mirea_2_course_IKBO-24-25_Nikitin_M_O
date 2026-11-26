"""Command-line entry point for the YAML translator."""

import sys

from src.errors import ConfigError
from src.translator import translate


def main() -> int:
    """Run the translator and return the process exit code."""
    source = sys.stdin.read()
    try:
        sys.stdout.write(translate(source))
    except ConfigError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
