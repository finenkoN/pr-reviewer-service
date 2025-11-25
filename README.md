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
- Make (опционально)

### Запуск через Docker Compose

```bash
# Собрать и запустить сервис
docker-compose up --build

# Или через Make
make build
make up
```

Сервис будет доступен на `http://localhost:8080`

API документация: `http://localhost:8080/docs`

### Остановка

```bash
docker-compose down

# Или
make down
```

## Использование Makefile

```bash
make build          # Собрать Docker образы
make up             # Запустить сервис
make down           # Остановить сервис
make logs           # Просмотр логов
make test           # Запустить тесты
make test-integration  # Запустить интеграционные тесты
make lint           # Проверить код линтером
make format         # Отформатировать код
make migrate        # Применить миграции
make clean          # Очистить проект
make load-test      # Нагрузочное тестирование (требует запущенный сервис)
```

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

## Принятые решения и допущения

### 1. Язык и фреймворк

**Решение**: Python + FastAPI вместо Go

**Обоснование**:
- Быстрая разработка и прототипирование
- Отличная поддержка OpenAPI из коробки
- Простота написания тестов
- Хорошая экосистема для работы с БД

### 2. База данных

**Решение**: PostgreSQL

**Обоснование**:
- Соответствует предпочтениям задания
- Надежность и ACID гарантии
- Хорошая поддержка в SQLAlchemy

### 3. Назначение ревьюверов

**Решение**: Случайный выбор из активных участников команды

**Обоснование**:
- Равномерное распределение нагрузки
- Простота реализации
- В задании не указан конкретный алгоритм

### 4. Переназначение ревьюверов

**Решение**: Новый ревьювер выбирается из команды заменяемого ревьювера

**Обоснование**:
- Соответствует требованиям задания
- Обеспечивает сохранение контекста команды

### 5. Идемпотентность merge

**Решение**: Повторный вызов merge возвращает текущее состояние PR без ошибки

**Обоснование**:
- Соответствует требованиям задания
- Упрощает интеграцию с внешними системами

### 6. Массовая деактивация

**Решение**: Автоматическое переназначение ревьюверов для открытых PR перед деактивацией

**Обоснование**:
- Обеспечивает безопасность открытых PR
- Минимизирует ручную работу
- Оптимизировано для средних объемов данных (< 100 мс)

### 7. Обработка ошибок

**Решение**: Кастомные исключения с кодами ошибок согласно OpenAPI спецификации

**Обоснование**:
- Соответствие спецификации
- Четкая структура ошибок
- Удобство отладки

## Производительность

### SLI требования

- **RPS**: 5 запросов в секунду
- **Время ответа**: < 300 мс (p99)
- **Успешность**: 99.9%

### Оптимизации

1. Индексы на часто используемые поля (user_id, team_name, status)
2. Эффективные запросы с использованием SQLAlchemy
3. Минимальное количество запросов к БД
4. Оптимизация массовой деактивации (батчинг операций)

## Линтинг

Проект использует **Ruff** для линтинга и форматирования кода.

Конфигурация в `pyproject.toml` и `.ruff.toml`.

```bash
# Проверка
make lint

# Форматирование
make format
```

## Дополнительные задания

✅ **Статистика** - реализован endpoint `/stats`
✅ **Нагрузочное тестирование** - скрипт для Locust в `tests/load_test.py`
✅ **Массовая деактивация** - endpoint `/users/bulkDeactivate`
✅ **Интеграционные тесты** - полный набор тестов в `tests/integration/`
✅ **Конфигурация линтера** - Ruff настроен в `pyproject.toml`

## Разработка

### Локальная разработка без Docker

```bash
# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows

# Установить зависимости
pip install -r requirements.txt

# Настроить переменные окружения
export DATABASE_URL="postgresql://pr_reviewer:pr_reviewer_pass@localhost:5432/pr_reviewer_db"

# Применить миграции
alembic upgrade head

# Запустить сервис
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### Создание миграций

```bash
# Создать новую миграцию
make migrate-create message="описание изменений"

# Или напрямую
alembic revision --autogenerate -m "описание изменений"
```

## Лицензия

Тестовое задание для стажировки.

