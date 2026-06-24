# Мам, это инвестиция

Сервис для коллекционеров комиксов, манги, книг, фигурок и карточек. Пользователь ведёт коллекции и wishlist, создаёт заявки на отсутствующие позиции каталога, а модераторы превращают заявки в нормализованные `CatalogItem` и `CatalogVariant`.

## Стек

- Backend: FastAPI, SQLAlchemy async, Alembic, PostgreSQL, Pydantic, JWT.
- Frontend: Next.js App Router, TypeScript, Tailwind, TanStack Query, React Hook Form, Zod.
- Infra: Docker Compose.

## Требования

- Docker
- Docker Compose

## Быстрый запуск

```bash
cp .env.example .env
docker compose up --build
```

После старта:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Swagger: http://localhost:8000/docs
- OpenAPI: http://localhost:8000/openapi.json
- Health: http://localhost:8000/health
- Readiness: http://localhost:8000/ready

Backend-контейнер при запуске выполняет:

```bash
alembic upgrade head
python -m app.scripts.seed_dev
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Seed идемпотентный: повторный запуск не создаёт дубликаты.

## Dev-пользователи

Все пароли для локального development:

```text
password123
```

Пользователи:

```text
user@example.com
moderator@example.com
senior@example.com
admin@example.com
```

## Миграции

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend alembic downgrade base
```

Для обычной разработки downgrade до base нужен редко: он удаляет все таблицы и данные.

## Seed

Seed запускается автоматически в `docker compose up`, но его можно выполнить вручную:

```bash
docker compose exec backend python -m app.scripts.seed_dev
```

Seed создаёт роли, категории, атрибуты, справочники, один catalog item, несколько variants, коллекцию, wishlist item и pending-заявку.

## Тесты

Backend:

```bash
make lint
make typecheck
make test
```

Frontend:

```bash
cd frontend
npm run lint
npm run typecheck
npm run test
npm run build
```

## Структура

```text
backend/   FastAPI, SQLAlchemy, Alembic
frontend/  Next.js приложение
docker-compose.yml
.env.example
.github/workflows/ci.yml
```

## Роли

- `user`: коллекции, wishlist, заявки.
- `moderator`: очередь модерации, reject/duplicate.
- `senior_moderator`: approve и создание catalog item/variant.
- `admin`: админские справочники и метаданные.

## Известные ограничения

- Access token хранится во frontend в `localStorage`, это удобно для dev, но не production-grade.
- Нет media API, Telegram-бота, парсера цен, платежей и marketplace.
- Основной поиск пока SQL-based, без Elasticsearch.
- Rate limiting login пока не внедрён.
