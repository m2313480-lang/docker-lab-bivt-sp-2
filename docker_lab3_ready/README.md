# Лабораторная работа 3 — Event-driven архитектура, RabbitMQ

## Что здесь сделано

В проекте подняты 3 контейнера:

- `rabbitmq-standalone-lab3` — RabbitMQ + Management UI
- `user-service` — producer, REST API, отправляет событие `USER_CREATED`
- `notification-service` — consumer, слушает очередь `user.events` и логирует уведомление

Схема:

```text
POST /users
↓
user-service
↓ событие user.created
RabbitMQ exchange user.exchange
↓
queue user.events
↓
notification-service
```

---

## Как запустить

Перейти в папку `compose`:

```powershell
cd compose
```

Запустить:

```powershell
docker compose up --build
```

Проверить контейнеры:

```powershell
docker ps
```

Должны быть:

- `rabbitmq-standalone-lab3`
- `compose-user-service-1`
- `compose-notification-service-1`

---

## RabbitMQ UI

Открыть:

```text
http://localhost:15672
```

Логин:

```text
guest
```

Пароль:

```text
guest
```

---

## Проверка приложения

Открыть:

```text
http://localhost:8080
```

Создать пользователя через PowerShell:

```powershell
Invoke-RestMethod -Method POST -Uri http://localhost:8080/users -ContentType "application/json" -Body '{"name":"Тацишин Михаил Сергеевич","email":"m2313480@edu.misis.ru"}'
```

После этого в логах `notification-service` должно появиться сообщение о полученном событии.

Логи можно посмотреть:

```powershell
docker logs compose-notification-service-1
```

---

# Что создать вручную в RabbitMQ UI для защиты

По заданию нужно создать exchange, queue и bindings через UI.

Данные можно использовать такие:

```text
Группа: bivt
Номер: 1
```

Если у тебя другой номер в списке — замени `1` на свой.

---

## 1. Queue

Вкладка:

```text
Queues and Streams
```

Создать очередь:

```text
queue.bivt.1
```

---

## 2. Fanout exchange

Вкладка:

```text
Exchanges
```

Создать exchange:

```text
bivt.1.fanout
```

Type:

```text
fanout
```

Binding к очереди:

```text
queue.bivt.1
```

Routing key оставить пустым.

Проверка: отправить сообщение в fanout exchange с любым routing key. Оно должно попасть в очередь.

---

## 3. Direct exchange

Создать exchange:

```text
bivt.1.direct
```

Type:

```text
direct
```

Binding к очереди:

```text
queue.bivt.1
```

Routing key:

```text
bivt.1.routing.key
```

Проверка:

- сообщение с routing key `bivt.1.routing.key` попадёт в очередь
- сообщение с другим routing key не попадёт

---

## 4. Topic exchange

Создать exchange:

```text
bivt.1.topic
```

Type:

```text
topic
```

Binding к очереди:

```text
queue.bivt.1
```

Routing key:

```text
bivt.*.routing.key
```

Проверка:

- `bivt.1.routing.key` попадёт
- `bivt.abc.routing.key` попадёт
- `bivt.1.extra.routing.key` не попадёт, потому что `*` заменяет только одно слово

---

## 5. Headers exchange

Создать exchange:

```text
bivt.1.headers
```

Type:

```text
headers
```

Binding к очереди:

```text
queue.bivt.1
```

Headers:

```text
x-match = all
group = bivt
number = 1
```

Проверка:

Сообщение попадёт в очередь только если в headers есть оба поля:

```text
group=bivt
number=1
```

---

# Какие скрины сделать

Для защиты сделай реальные скрины:

1. Docker Desktop / `docker ps`, где видны RabbitMQ и сервисы
2. RabbitMQ UI — список Exchanges
3. RabbitMQ UI — список Queues
4. Страница очереди `queue.bivt.1` с bindings
5. Проверка отправки сообщений в очередь
6. Логи notification-service после POST `/users`

---

# Что говорить на защите

## Что такое RabbitMQ

RabbitMQ — брокер сообщений. Он принимает сообщения от producer, маршрутизирует их через exchange и кладёт в queue, откуда их забирает consumer.

## Что такое Event-driven architecture

Event-driven architecture — архитектура, где сервисы общаются через события. Один сервис публикует событие, другой сервис его получает и обрабатывает.

## Producer и Consumer

Producer — сервис, который отправляет сообщение.

Consumer — сервис, который читает сообщение из очереди.

В этой работе:

- `user-service` — producer
- `notification-service` — consumer
- RabbitMQ — брокер сообщений

## Exchange

Exchange принимает сообщение и решает, в какую очередь его направить.

## Queue

Queue хранит сообщения, пока consumer их не прочитает.

## Binding

Binding — правило связи между exchange и queue.

## Routing key

Routing key — ключ маршрутизации сообщения. По нему RabbitMQ понимает, подходит ли сообщение под binding.

## Fanout exchange

Отправляет сообщение во все привязанные очереди. Routing key не важен.

## Direct exchange

Отправляет сообщение только если routing key полностью совпадает с binding key.

## Topic exchange

Похож на direct, но поддерживает шаблоны:

- `*` — одно слово
- `#` — ноль или больше слов

## Headers exchange

Маршрутизирует сообщения по headers, а не по routing key.

---

# Как остановить

```powershell
docker compose down
```
