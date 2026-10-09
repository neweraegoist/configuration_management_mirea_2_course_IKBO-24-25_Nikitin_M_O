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
