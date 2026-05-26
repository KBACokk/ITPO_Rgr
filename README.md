# Неделя 17 — финальный проект (bookings-s11)

Демонстрационная система из **трёх микросервисов**: REST API Gateway, gRPC-сервис бронирований (`BookingsService`, порт **8272** по варианту), gRPC-сервис доступности слотов. Подробная схема — в [ARCHITECTURE.md](./ARCHITECTURE.md).

## Быстрый старт (одна команда)

Из каталога `weeks/week-17` (нужны Docker и Docker Compose plugin):

```bash
docker compose up --build
```

После сборки HTTP API доступен на **http://localhost:8080**.

### Примеры запросов

Проверка шлюза:

```bash
curl -s http://localhost:8080/health
```

Создание брони (`date` — строка по контракту варианта):

```bash
curl -s -X POST http://localhost:8080/api/bookings ^
  -H "Content-Type: application/json" ^
  -d "{\"resource_id\":\"room-A\",\"date\":\"2026-06-15\",\"title\":\"Planning\"}"
```

В Unix/macOS замените переносы на `\` для bash.

Список броней:

```bash
curl -s http://localhost:8080/api/bookings
```

Документация OpenAPI: **http://localhost:8080/docs**

## Структура каталога

| Путь | Назначение |
|------|------------|
| `proto/` | Исходники `.proto` |
| `gen/` | Сгенерированные `*_pb2.py` и `*_pb2_grpc.py` |
| `services/gateway/` | FastAPI + uvicorn |
| `services/bookings_service/` | gRPC BookingsService |
| `services/availability_service/` | gRPC AvailabilityService |
| `docker-compose.yml` | Локальный запуск всего стека |
| `chart/` | Опциональный Helm chart для Kubernetes |
| `CI.md` | Описание CI |

## Вариант студента

Файл задания: `variants/<GROUP>/<STUDENT_ID>/week-17.json`. В документ `ARCHITECTURE.md` должен входить **`project_code`** из этого файла (для проверки `make test WEEK=17`). Для группы **432** и студента **s11** код проекта — **bookings-s11**.

Переменные окружения для pytest/coursekit (если отличаются):

```bash
set GROUP=432
set STUDENT_ID=s11
```

