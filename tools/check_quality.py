"""Проверяет комментарии Python, сложность Radon и сообщения коммитов."""

import io
import re
import subprocess
import tokenize
from pathlib import Path

from radon.complexity import cc_visit

ROOT = Path(__file__).resolve().parents[1]
MAX_COMPLEXITY = 10
COMMIT_PATTERN = re.compile(
    r"(?:build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)"
    r"\([a-z0-9][a-z0-9-]*\)!?: [^\s].*"
)


def _git_lines(*args: str) -> list[str]:
    """Возвращает строки вывода Git из корня репозитория."""
    result = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True,
        text=True, encoding="utf-8",
    )
    return result.stdout.splitlines()


def check_python() -> list[str]:
    """Ищет комментарии и функции со сложностью выше десяти."""
    errors = []
    for name in _git_lines("ls-files", "*.py"):
        source = (ROOT / name).read_text(encoding="utf-8")
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for token in tokens:
            if token.type == tokenize.COMMENT:
                errors.append(f"{name}:{token.start[0]}: Python comment")
        blocks = cc_visit(source)
        for block in list(blocks):
            blocks.extend(getattr(block, "methods", []))
            blocks.extend(getattr(block, "closures", []))
        for block in blocks:
            if block.complexity > MAX_COMPLEXITY:
                errors.append(
                    f"{name}:{block.lineno}: {block.name}: "
                    f"complexity {block.complexity} > {MAX_COMPLEXITY}"
                )
    return errors


def check_commits() -> list[str]:
    """Проверяет Conventional Commits с обязательной областью изменений."""
    errors = []
    for line in _git_lines("log", "--format=%h %s", "HEAD"):
        commit, subject = line.split(" ", 1)
        if COMMIT_PATTERN.fullmatch(subject) is None:
            errors.append(f"{commit}: invalid commit subject: {subject}")
    return errors


def main() -> int:
    """Выводит нарушения качества и возвращает код завершения проверки."""
    errors = check_python() + check_commits()
    if errors:
        print("\n".join(errors))
        return 1
    print("Python comments, cyclomatic complexity and commits: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
