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

## Код программы
```
sort -k2 -nr /etc/protocols | head -5
```

## Пояснение
```
sort -k2 -nr  — сортируем по 2-му столбцу, от большего к меньшему. 
head -5  — берём первые 5 строк.
```

## Результат вывода
```
rohc	 142	ROHC		# Robust Header Compression
wesp	 141	WESP		# Wrapped Encapsulating Security Payload
shim6	 140	Shim6		# Shim6 Protocol [RFC5533]
hip	     139	HIP		    # Host Identity Protocol
manet	 138			    # MANET Protocols [RFC5498]
```
