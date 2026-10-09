# Задача 1

## Вывести отсортированный в алфавитном порядке список имен пользователей в файле passwd (вам понадобится grep).


### Код программы
```
grep -o '^[^:]*' /etc/passwd | sort
```

### Результат вывода
```
apt
avahi
backup
bin
colord
daemon
games
gnats
irc
labex
list
lp
mail
man
messagebus
mongodb
mysql
news
nobody
proxy
pulse
redis
root
rtkit
saned
sshd
sync
sys
systemd-network
systemd-resolve
systemd-timesync
tcpdump
usbmux
uucp
www-data
```



# Задача 2

## Вывести данные /etc/protocols в отформатированном и отсортированном порядке для 5 наибольших портов, как показано в примере ниже:

```
[root@localhost etc]# cat /etc/protocols ...
142 rohc
141 wesp
140 shim6
139 hip
138 manet
```

### Код программы
```
sort -k2 -nr /etc/protocols | head -5
```

### Результат вывода
```
rohc	 142	ROHC		# Robust Header Compression
wesp	 141	WESP		# Wrapped Encapsulating Security Payload
shim6	 140	Shim6		# Shim6 Protocol [RFC5533]
hip	     139	HIP		    # Host Identity Protocol
manet	 138			    # MANET Protocols [RFC5498]
```



# Задание 3

##  Написать программу banner средствами bash для вывода текстов, как в следующем примере (размер баннера должен меняться!):
```
[root@localhost ~]# ./banner "Hello from RTU MIREA!"
+-----------------------+
| Hello from RTU MIREA! |
+-----------------------+
```
Перед отправкой решения проверьте его в ShellCheck на предупреждения.
### Код программы
```
nano banner
```
```
#!/bin/bash

text=$*
length=${#text}

# Формирование символов рамки от 1 до длины слова + 2 пробела
for _ in $(seq 1 $((length + 2))); do
    line+="-"
done

echo "+${line}+"
echo "| ${text} |"
echo "+${line}+"
```
```
chmod +x banner
./banner "Hello from RTU MIREA!"
```

### Результат вывода
```
+----------------------+
| Hello from RTU MIREA |
+----------------------+
```



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
# Запуск программы:

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



# Задача 5 

## Написать программу для регистрации пользовательской команды (правильные права доступа и копирование в /usr/local/bin). Например, пусть программа называется reg:
```
./reg banner
```
В результате для banner задаются правильные права доступа и сам banner копируется в /usr/local/bin.

### Код программы
```
nano banner
```
```
#!/bin/bash

text=$*
length=${#text}

# Формирование символов рамки от 1 до длины слова + 2 пробела
for _ in $(seq 1 $((length + 2))); do
    line+="-"
done

echo "+${line}+"
echo "| ${text} |"
echo "+${line}+"
```

```
nano reg
```
```
#!/bin/bash
# 755 - Чтение, запись, исполнение - Владалец | Чтение, исполнение - Другие пользователи
chmod 755 "$1"
# Копируем команду в /usr/local/bin
sudo cp "$1" /usr/local/bin/
```
```
# Запуск программы:

chmod +x banner
chmod +x reg
./reg banner
banner Hello
```

### Результат вывода
```
+-------+
| Hello |
+-------+
```



# Задача 6

## Написать программу для проверки наличия комментария в первой строке файлов с расширением c, js и py.

### Код программы
```
nano comments
```
```
#!/bin/bash

for file in *.c *.js *.py; do
    # Чтение первой строки с начала
    line=$(head -n 1 "$file")
    if [[ $line == "#"* || $line == "//"* || $line == "/*"* ]]; then
        echo "Файл $file начинается с комментария"
    else
        echo "Файл $file не начинается с комментария"
    fi
done
```
```
chmod +x comments
./comments
```



# Задача 7

## Написать программу для нахождения файлов-дубликатов (имеющих 1 или более копий содержимого) по заданному пути (и подкаталогам).

### Код программы
```
nano duplic
```
```
# Хеш-таблица
declare -A duplicats

# Рекурсивная функция для поиска и вывода дубликатов
findDuplicates() 
{
    local dir="$1"
    
    # Перебираем все файлы и подкаталоги в данном каталоге
    for file in "$dir"/*; do
        # Если файл
        if [[ -f "$file" ]]; then
            # оставляем только имя файла
            file=$(basename "$file")
            if [ duplicats["$file"] ]; then
                # Добавляем +1
                duplicats["$file"]=$((duplicats["$file"] + 1))
            else
                duplicats["$file"]=1
            fi

            if [ "${duplicats["$file"]}" -eq 2 ]; then
                echo "Файл-дубликат - '$file'"
            fi
        # Если подкаталог
        elif [[ -d "$file" ]]; then
            # Рекурсивно вызываем данную функцию
            findDuplicates "$file"
        fi
    done
}

findDuplicates "."
```

```
chmod +x duplic
./dupic
```



# Задача 8

## Написать программу, которая находит все файлы в данном каталоге с расширением, указанным в качестве аргумента и архивирует все эти файлы в архив tar.

### Код программы
```
nano archive
```
```
#!/bin/bash

# Ищем все файлы с заданным расширением в текущем каталоге и сохраняем их в массиве
files=( $(find . -type f -name "*.$1") )

# Создаем архив файлов без повторений
tar -cvf "archive.tar" "${files[@]}"

echo "Архив создан"
```
```
chmod +x archive
./archive
```
### Результат вывода
```
tar: Cowardly refusing to create an empty archive
Try 'tar --help' or 'tar --usage' for more information.
Архив создан
```



# Задача 9

## Написать программу, которая заменяет в файле последовательности из 4 пробелов на символ табуляции. Входной и выходной файлы задаются аргументами.

### Код программы
```
nano replace
```
```
#!/bin/bash

# sed s/что_заменять/на_что_заменять/опции
# g - Замените все вхождения строки в файле
# > - передача вывода второму аргументу
sed 's/    /\t/g' "$1" > "$2"

# Выводим сообщение об успешном завершении скрипта
echo "Файл исправлен"
```
```
chmod +x replace
./replace
```



# Задача 10

## Написать программу, которая выводит названия всех пустых текстовых файлов в указанной директории. Директория передается в программу параметром.

### Код программы
```
nano empty
```
```
#!/bin/bash

find "$1" -maxdepth 1 -type f -empty
```


