# Лабораторная работа 2 — KeyDB / Redis / Cache-aside

Готовая лабораторная работа по кэшированию через KeyDB. KeyDB полностью совместим с Redis API.

## Что внутри

- Flask-приложение с CRUD для пользователей.
- PostgreSQL как основная база данных.
- KeyDB как Redis-compatible кэш.
- Реализована стратегия cache-aside:
  - первый `GET /users/<id>` читает пользователя из PostgreSQL и кладёт в KeyDB;
  - второй `GET /users/<id>` читает пользователя из кэша;
  - при `PUT` и `DELETE` кэш удаляется.
- Скрипты для создания Redis/KeyDB ключей по заданию.

## Запуск

Открыть терминал в папке проекта:

```powershell
cd "$HOME\OneDrive\Рабочий стол\docker_lab2\compose"
docker compose up --build
```

Если папка называется иначе, зайдите в свою папку и затем в `compose`.

После запуска открыть:

```text
http://localhost:8080
```

## Проверить контейнеры

В новом PowerShell:

```powershell
docker ps
```

Должны быть контейнеры:

- `api-demo`
- `postgres`
- `keydb`

## Создать пользователя

В новом PowerShell:

```powershell
curl.exe -X POST http://localhost:8080/users -H "Content-Type: application/json" -d "{\"name\":\"Ivan Ivanov\",\"email\":\"student@misis.edu\"}"
```

В ответе будет `id`. Скопируйте его.

## Проверить cache-aside

Первый запрос:

```powershell
curl.exe http://localhost:8080/users/PASTE_ID_HERE
```

В ответе будет:

```json
"source": "database"
```

Второй запрос:

```powershell
curl.exe http://localhost:8080/users/PASTE_ID_HERE
```

В ответе будет:

```json
"source": "cache"
```

Проверить TTL кэша:

```powershell
curl.exe http://localhost:8080/cache/PASTE_ID_HERE
```

Обновить пользователя и очистить кэш:

```powershell
curl.exe -X PUT http://localhost:8080/users/PASTE_ID_HERE -H "Content-Type: application/json" -d "{\"name\":\"New Name\"}"
```

Удалить пользователя и очистить кэш:

```powershell
curl.exe -X DELETE http://localhost:8080/users/PASTE_ID_HERE
```

## Работа с KeyDB через keydb-cli / redis-cli

Зайти в контейнер KeyDB:

```powershell
docker exec -it keydb sh
```

Открыть CLI:

```sh
keydb-cli
```

Примеры команд:

```redis
SET student:bivt-sp-2:1 "Ivan Ivanov"
GET student:bivt-sp-2:1
EXPIRE student:bivt-sp-2:1 60
TTL student:bivt-sp-2:1
PERSIST student:bivt-sp-2:1

HSET student:bivt-sp-2:1:info name "Ivan Ivanov" age "18" email "student@misis.edu"
HGETALL student:bivt-sp-2:1:info
HGET student:bivt-sp-2:1:info name

RPUSH student:bivt-sp-2:1:timetable "Architecture" "Databases" "Programming"
LPUSH student:bivt-sp-2:1:timetable "Math"
LRANGE student:bivt-sp-2:1:timetable 0 -1
LPOP student:bivt-sp-2:1:timetable

SADD student:bivt-sp-2:1:skills Docker Python Redis PostgreSQL
SMEMBERS student:bivt-sp-2:1:skills
SREM student:bivt-sp-2:1:skills Python

ZADD student:bivt-sp-2:1:tasks_w_priority 100 "Сделать лабу 1" 150 "Сделать лабу 2" 50 "Загрузить на GitHub"
ZRANGE student:bivt-sp-2:1:tasks_w_priority 0 -1 WITHSCORES
ZRANGE student:bivt-sp-2:1:tasks_w_priority -1 -1 WITHSCORES
ZINCRBY student:bivt-sp-2:1:tasks_w_priority 100 "Загрузить на GitHub"
ZREM student:bivt-sp-2:1:tasks_w_priority "Загрузить на GitHub"
```

Выйти из CLI:

```redis
exit
```

## Быстро создать все ключи для задания

Скопируйте скрипт в контейнер и запустите:

```powershell
docker cp ..\keydb_commands.sh keydb:/keydb_commands.sh
docker exec -it keydb sh /keydb_commands.sh
```

Перед защитой можно поменять в `keydb_commands.sh` группу, номер, ФИО, возраст и email.

## Получить вывод всех ключей для отчёта

```powershell
docker cp ..\scan_keys.sh keydb:/scan_keys.sh
docker exec -it keydb sh /scan_keys.sh
```

В выводе будут ключи, типы и значения.

## Что показывать преподавателю

1. Docker Desktop — `Engine running`.
2. `docker ps` — три контейнера: приложение, PostgreSQL, KeyDB.
3. `docker-compose.yaml` — там описаны `api-demo`, `postgres`, `keydb`.
4. `Dockerfile` — как собирается приложение.
5. KeyDB CLI — созданные ключи: string, hash, list, set, zset.
6. Вывод `scan_keys.sh`.
7. Работа cache-aside:
   - первый запрос пользователя — `source: database`;
   - второй запрос — `source: cache`;
   - после обновления/удаления кэш очищается.
8. GitHub репозиторий с проектом.

## Короткие ответы к защите

### Что такое кэширование?

Кэширование — это сохранение часто используемых данных в быстром хранилище, чтобы не ходить каждый раз в медленную базу данных.

### Зачем используется Redis / KeyDB?

Redis/KeyDB — это in-memory key-value хранилище. Оно хранит данные в оперативной памяти, поэтому работает очень быстро. Его используют для кэша, сессий, очередей, счётчиков.

### Какие типы данных есть?

String, Hash, List, Set, Sorted Set/ZSet.

### Что такое cache-aside?

Cache-aside — стратегия, где приложение сначала смотрит в кэш. Если данных нет, оно идёт в БД, получает данные и кладёт их в кэш. При обновлении или удалении данных кэш очищается.

### Почему при обновлении нужно удалять кэш?

Чтобы не вернуть пользователю устаревшие данные.

### Что такое TTL?

TTL — время жизни ключа. Когда TTL заканчивается, ключ автоматически удаляется.

## Остановка

В папке `compose`:

```powershell
docker compose down
```
