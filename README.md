# configuration_management_mirea_2_course_IKBO-24-25_Nikitin_M_O

Практические работы по дисциплине «Конфигурационное управление», вариант 16.

- [Практическая работа №1: эмулятор командной строки](Practice%201/config-shell-emu/README.md).
- [Практическая работа №2: граф зависимостей Maven](Practice%202/dependency-graph-tool/README.md).

## Проверка всех работ

Для запуска проверок нужен Python 3.12. Команды выполняются из корня репозитория:

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check --no-respect-gitignore .
python tools/check_quality.py
python -m pytest -v
```

Ruff проверяет оформление PEP8, имена, docstring и сложность функций.
Дополнительная проверка запрещает комментарии в Python-файлах, измеряет
цикломатическую сложность через Radon (не выше 10) и проверяет всю историю
на формат `type(scope): description`.

В тестах первой работы импорты модулей эмулятора следуют за настройкой
`sys.path`, чтобы сохранить прямой запуск через `unittest`. Поэтому только
для этих файлов в `pyproject.toml` разрешён E402; комментарии `noqa` не нужны.

В GitHub Actions эти же проверки запускаются при push и pull request.
