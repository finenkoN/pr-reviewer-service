# PR Reviewer Assignment Service

Микросервис для автоматического назначения ревьюверов на Pull Request'ы.

## Описание

Сервис предоставляет HTTP API для:
- Управления командами и пользователями
- Автоматического назначения ревьюверов на PR (до 2 из команды автора)
- Переназначения ревьюверов
- Получения списка PR для пользователя
- Статистики по сервису
- Массовой деактивации пользователей команды

## Технологии

- **Python 3.13** с **FastAPI**
- **PostgreSQL** для хранения данных
- **SQLAlchemy** для ORM
- **Alembic** для миграций БД
- **Docker & Docker Compose** для развертывания

## Быстрый старт

### Требования

- Docker и Docker Compose
- Make

### Запуск через Docker Compose

```bash
docker-compose up --build

# Или через Make
make build
make up
```

Сервис будет доступен на `http://localhost:8080`



## API Endpoints

### Команды

- `POST /team/add` - Создать команду с участниками
- `GET /team/get?team_name=<name>` - Получить команду

### Пользователи

- `POST /users/setIsActive` - Установить флаг активности пользователя
- `GET /users/getReview?user_id=<id>` - Получить PR'ы пользователя как ревьювера
- `POST /users/bulkDeactivate` - Массовая деактивация команды (дополнительно)

### Pull Requests

- `POST /pullRequest/create` - Создать PR и назначить ревьюверов
- `POST /pullRequest/merge` - Пометить PR как MERGED (идемпотентно)
- `POST /pullRequest/reassign` - Переназначить ревьювера

### Дополнительные

- `GET /stats` - Статистика сервиса
- `GET /health` - Проверка здоровья сервиса

Полная спецификация API доступна в `openapi.yaml` и в Swagger UI (`/docs`).

## Примеры использования

### Создание команды

```bash
curl -X POST "http://localhost:8080/team/add" \
  -H "Content-Type: application/json" \
  -d '{
    "team_name": "backend",
    "members": [
      {"user_id": "u1", "username": "Alice", "is_active": true},
      {"user_id": "u2", "username": "Bob", "is_active": true}
    ]
  }'
```

### Создание PR

```bash
curl -X POST "http://localhost:8080/pullRequest/create" \
  -H "Content-Type: application/json" \
  -d '{
    "pull_request_id": "pr-1",
    "pull_request_name": "Add feature",
    "author_id": "u1"
  }'
```

### Получение статистики

```bash
curl "http://localhost:8080/stats"
```

## Тестирование

### Интеграционные тесты

```bash
# Запуск всех тестов
make test

# Только интеграционные
make test-integration

# Или напрямую
pytest tests/ -v
```

### Нагрузочное тестирование

```bash
# Запустить сервис
make up

# В другом терминале запустить Locust
make load-test

# Открыть http://localhost:8089 в браузере
```

## Структура проекта

```
pr_reviewer_service/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI приложение
│   ├── database.py       # Настройка БД
│   ├── models.py         # SQLAlchemy модели
│   ├── schemas.py        # Pydantic схемы
│   ├── services.py       # Бизнес-логика
│   └── exceptions.py     # Исключения
├── migrations/           # Миграции Alembic
│   ├── versions/
│   └── env.py
├── tests/
│   ├── integration/      # Интеграционные тесты
│   ├── conftest.py       # Фикстуры pytest
│   └── load_test.py      # Скрипт для Locust
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── requirements.txt
├── alembic.ini
├── openapi.yaml
└── README.md
```

## Принятые решения

###  Назначение ревьюверов

**Решение**: Случайный выбор из активных участников команды

**Обоснование**:
- Равномерное распределение нагрузки
- В задании не указан конкретный алгоритм




## Производительность

### SLI требования

- **RPS**: 5 запросов в секунду
- **Время ответа**: < 300 мс (p99)
- **Успешность**: 99.9%

### Оптимизации

1. Индексы на часто используемые поля (user_id, team_name, status)
2. Оптимизация массовой деактивации (батчинг операций)

## Линтинг

Проект использует **Ruff** для линтинга и форматирования кода.

Конфигурация в `pyproject.toml` и `.ruff.toml`.

```bash
make lint

make format
```

## Дополнительные задания

 **Статистика** - реализован endpoint `/stats`
 
 **Нагрузочное тестирование** - скрипт для Locust в `tests/load_test.py`
   - **Целевой RPS:** 5.0 (достигнуто: 5.2).
   - **Всего запросов:** ~1500
   - **Время ответа (p99):** 125 мс (требование: < 300 мс).
   - **Успешность:** 99.95%.
 **Массовая деактивация** - endpoint `/users/bulkDeactivate`
 
 **Интеграционные тесты** - полный набор тестов в `tests/integration/`
 
 **Конфигурация линтера** - Ruff настроен в `pyproject.toml`


## Создание миграций

```bash
make migrate-create message="описание изменений"

alembic revision --autogenerate -m "описание изменений"
```
