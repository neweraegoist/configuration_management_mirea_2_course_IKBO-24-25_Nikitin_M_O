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
