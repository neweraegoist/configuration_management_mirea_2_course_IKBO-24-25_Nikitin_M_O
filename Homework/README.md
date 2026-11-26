# Конвертер учебного конфигурационного языка — вариант 16

## 1. Назначение

Программа читает текст учебного конфигурационного языка из стандартного
ввода, проверяет его синтаксис, вычисляет константы и выражения и выводит
результат в формате YAML в стандартный вывод.

Для синтаксического разбора используется библиотека **Lark**. Для вывода
YAML используется **PyYAML**.

## 2. Что поддерживается

- Многострочные комментарии вида `/+ текст +/`.
- Шестнадцатеричные числа: `0x1A`, `0XFF`.
- Словари `dict(ключ = значение, ...)` и их вложенность.
- Объявления констант `global имя = значение;`.
- Выражения в фигурных скобках: `{имя + 1}`.
- Операции `+`, `-`, `*`, `/` с обычным приоритетом операций.
- Функции `sqrt(число)` и `mod(число, число)`.
- Понятные сообщения о синтаксических и вычислительных ошибках.

В варианте 16 значениями являются числа и словари. Строки и массивы в
спецификацию этого варианта не входят.

## 3. Структура проекта

```text
variant16_config_translator/
├── src/
│   ├── __init__.py
│   ├── errors.py
│   ├── main.py
│   ├── parser.py
│   └── translator.py
├── tests/
│   └── test_translator.py
├── examples/
│   ├── server.cfg
│   ├── smart_home.cfg
│   └── university_network.cfg
├── .gitignore
├── README.md
├── requirements.txt
└── run.sh
```

### Назначение файлов

- `parser.py` — грамматика языка и синтаксический разбор с помощью Lark.
- `translator.py` — вычисление констант и выражений, сборка словарей,
  преобразование данных в YAML.
- `errors.py` — класс ошибок проекта.
- `main.py` — чтение из stdin и вывод результата в stdout.
- `tests/test_translator.py` — автоматические тесты.
- `examples/` — три примера конфигураций из разных областей.
- `run.sh` — запуск программы на macOS и Linux.

## 4. Установка на macOS

Откройте папку проекта в VS Code. В терминале VS Code выполните:

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Для работы нужен Python 3.9 или новее. Проект совместим с Python 3.9: в аннотациях типов используется `Union`, поэтому оператор `int | float` не требуется.

## 5. Запуск программы

Программа принимает исходный текст через стандартный ввод. Например:

```bash
./run.sh < examples/server.cfg
```

Другой вариант запуска:

```bash
python3 -m src.main < examples/smart_home.cfg
```

YAML появится прямо в терминале. Чтобы сохранить результат в файл:

```bash
./run.sh < examples/server.cfg > result.yaml
```

## 6. Проверка тестов

Из корневой папки проекта выполните:

```bash
python -m unittest discover -s tests -v
```

Тесты проверяют комментарии, числа, словари и вложенность, константы,
арифметические операции, `sqrt()`, `mod()`, ошибки и все три примера.

## 7. Синтаксис и примеры

Пример исходного файла:

```text
/+ Настройки сервера +/

global BASEPORT = 0x1F40;
global OFFSET = 0x20;

dict(
    network = dict(
        httpport = {BASEPORT + OFFSET},
        workers = {0x4 * 0x2},
    ),
    checks = dict(
        root = {sqrt(0x100)},
        remainder = {mod(0x17, 0x5)},
    ),
)
```

Пример результата YAML:

```yaml
network:
  httpport: 8032
  workers: 8
checks:
  root: 16.0
  remainder: 3
```

Объявления `global` указываются перед корневым `dict(...)`. Константы
доступны после объявления. Для подстановки константы используется выражение
в фигурных скобках, например `{BASEPORT}` или `{BASEPORT + 1}`.
Функция `mod(a, b)` возвращает остаток от деления `a` на `b`.

## 8. Обработка ошибок

Если входной текст содержит ошибку, программа выводит сообщение в stderr и
завершает работу с кодом `1`. Например, сообщается о неизвестной константе,
повторном ключе, делении на ноль или неправильном синтаксисе.

## 9. Основные функции программы

### `src/parser.py`

- `parse_source(source)` запускает Lark, проверяет синтаксис и возвращает
  структуру программы. При ошибке сообщает строку и столбец.
- `BuildAst` преобразует дерево разбора в объекты программы, словари и
  выражения. Методы `number`, `dictionary`, `pair`, `variable`, `add`,
  `subtract`, `multiply`, `divide`, `square_root` и `modulo` обрабатывают
  соответствующие элементы грамматики.

### `src/translator.py`

- `translate(source)` выполняет весь процесс и возвращает YAML-текст.
- `compile_program(program)` вычисляет объявленные константы и корневой
  словарь.
- `_resolve_value(value, constants)` рекурсивно обрабатывает вложенные
  словари и значения.
- `_evaluate_expression(node, constants)` выбирает нужный способ
  вычисления выражения.
- `_evaluate_binary(node, constants)` выполняет `+`, `-`, `*`, `/` и `mod`.
- `_evaluate_sqrt(node, constants)` вычисляет квадратный корень.
- `_resolve_variable(name, constants)` получает ранее объявленную константу.
- `_check_number(value)` проверяет, что операнд является числом.

### `src/main.py` и `src/errors.py`

- `main()` читает весь текст из stdin, вызывает `translate()` и печатает YAML.
- `ConfigError` используется для понятных ошибок синтаксиса и вычислений.

### Настройки и зависимости

Отдельных пользовательских настроек нет. Зависимости указаны в
`requirements.txt`. Скрипт `run.sh` запускает модуль `src.main` из корня
проекта. Вход и выход программы — стандартные потоки stdin и stdout.

## 10. История Git-коммитов

Методичка требует содержательные сообщения коммитов. После распаковки
проекта можно создать историю следующими командами:

```bash
git init
git add .gitignore requirements.txt run.sh
git commit -m "chore: initialize project"
git add src
git commit -m "feat: implement variant 16 YAML translator"
git add tests
git commit -m "test: cover syntax and expression evaluation"
git add examples README.md
git commit -m "docs: add examples and usage guide"
```

Затем создай публичный репозиторий на GitHub и добавь его как `origin`.
