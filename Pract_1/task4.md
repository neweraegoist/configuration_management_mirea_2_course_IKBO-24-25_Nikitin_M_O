# Задача 4

## Написать программу для вывода всех идентификаторов (по правилам C/C++ или Java) в файле (без повторений). Пример для hello.c:
```
h hello include int main n printf return stdio void world
```

### Код программы
```
nano hello.c
```
```
#include <stdio.h>

int main() {
    printf("Hello world");
    return 0;
}
```
```
nano ident
```
```
#!/bin/bash
file="$1"
ident=$(grep -o -E '\b[a-zA-Z]*\b' "$file" | sort -u)
echo "Идентификаторы:"
echo "$ident"
```
```
chmod +x ident
./ident hello.c
```

### Результат вывода
```
h
Hello
include
int
main
printf
return
stdio
world
```

### Пояснение
```

nano ident - создание скрипта

#!/bin/bash - нужно выполнять с помощью Bash
file="$1" - Создаёт переменную file и записывает в неё имя файла

ident=$(grep -o -E '\b[a-zA-Z]*\b' "$file" | sort -u) -Она находит слова в файле, сортирует их и убирает повторы
    ident= — сохраняем результат в переменную ident.
    $(...) — выполняем команды внутри скобок и сохраняем их вывод.
    grep — ищет совпадения в файле.
    -o — выводит только найденные совпадения, каждое отдельно.
    -E — включает расширенные регулярные выражения.
    '\b[a-zA-Z]*\b' — шаблон поиска.
    "$file" — файл, в котором ищем.
    | — передаёт результат одной команды следующей.
    sort -u — сортирует найденные слова и убирает повторения.

echo "Идентификаторы:"
echo "$ident"

Запуск программы:
chmod +x ident
./ident hello.c
```
