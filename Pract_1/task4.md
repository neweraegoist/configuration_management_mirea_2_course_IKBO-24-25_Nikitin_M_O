# Задача 4

## Написать программу для вывода всех идентификаторов (по правилам C/C++ или Java) в файле (без повторений). Пример для hello.c:
```
h hello include int main n printf return stdio void world
```

### Код программы
```
nano hello.c

#include <stdio.h>

int main() {
    printf("Hello world");
    return 0;
}
```
```
nano ident

#!/bin/bash
grep -oE '[a-zA-Z_][a-zA-Z0-9_]*' "$1" | sort -u

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
nano hello.c - создание файла

#include <stdio.h>
int main()
{
    printf("Hello world");
    return 0;
}

nano ident - создание скрипта

#!/bin/bash - скрипт нужно выполнять с помощью Bash
grep -oE '[a-zA-Z_][a-zA-Z0-9_]*' "$1" | sort -u

grep - Команда для поиска текста
-oE
  -o — выводить только найденные совпадения.
  -E — включить расширенные регулярные выражения.
'[a-zA-Z_][a-zA-Z0-9_]*' - ищет слова, которые начинаются с английской буквы или _, а дальше могут содержать буквы, цифры и _
"$1" - Это первый аргумент, переданный скрипту при запуске.
| - передаёт результат одной команды следующей
sort -u
  sort — сортирует строки по алфавиту.
  -u — оставляет только уникальные строки, убирая повторения.

chmod +x ident - изменяет права доступа к файлу, а +x добавляет право на выполнение.

./ident hello.c - запуск
```
