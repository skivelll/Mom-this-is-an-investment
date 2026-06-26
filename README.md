# Мам, это инвестиция

Сервис для коллекционеров комиксов, манги, книг, фигурок и карточек. Пользователь в первую очередь управляет содержимым личной коллекции, ведёт wishlist, ищет предметы в каталоге и создаёт заявки на отсутствующие позиции.

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

Если нужно поднять полностью отдельный стек, например для smoke/e2e, задавайте project name:

```bash
docker compose -p mom-investment-dev up --build
docker compose -p mom-investment-dev down -v
```

В `docker-compose.yml` нет фиксированных `container_name`, поэтому разные compose projects не конфликтуют по именам контейнеров и volumes.

После старта:

- Frontend: http://localhost:3100
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

## Пользовательская логика

После входа пользователь попадает в `Коллекцию`: это общий экран всех предметов из всех его коллекций, а не список контейнеров. Конкретная коллекция выбирается фильтром внутри страницы.

Приоритет основных разделов:

1. `Коллекция` — все личные предметы, поиск, фильтр по коллекции, редактирование личной записи.
2. `Wishlist` — желаемые предметы, поиск и фильтр по статусу.
3. `Каталог` — поиск новых предметов, добавление в коллекцию или wishlist.
4. `Мои заявки` — заявки на предметы, которых ещё нет в каталоге.

В интерфейсе предмет показывается как обычное название и, если нужно, короткая строка разновидности или издания. Внутренние сущности вроде catalog variant не являются центральным пользовательским понятием.

## Каталог, атрибуты и изображения

`CatalogItem` — базовый предмет каталога. Он может существовать без `CatalogVariant`: например, администратор или senior moderator может создать карточку "Chainsaw Man. Том 1", загрузить общую обложку и позже добавить конкретные издания.

`CatalogVariant` — конкретная разновидность предмета: язык, издание, регион, формат, производитель, лимитированная версия и другие отличия. Добавление в коллекцию и wishlist по-прежнему работает через variant, поэтому item без variants показывает понятное пустое состояние.

Атрибуты задаются через `Админка -> Атрибуты` и привязаны к категории. Frontend не хранит статический список атрибутов: формы каталога запрашивают актуальные definitions через backend и строят поля по `value_type`. Значения сохраняются в `catalog_item_attributes` или `catalog_variant_attributes` и возвращаются в responses item/variant.

Для `value_type=reference` у definition обязательно задан `reference_type`: `publisher`, `manufacturer`, `series` и так далее. Для остальных типов `reference_type` должен быть пустым. Backend проверяет, что выбранная `ReferenceEntity` существует и совпадает с ожидаемым типом. Ответ `GET /api/v1/admin/attributes?category_id=...` сразу содержит `reference_options`, поэтому frontend показывает в dynamic form только подходящие справочники и не выводит UUID пользователю.

Изображения используют существующий S3-compatible flow:

```text
POST /api/v1/media/catalog/upload-url
PUT  presigned URL в MinIO/S3
POST /api/v1/media/catalog
```

Управление изображениями доступно ролям `moderator`, `senior_moderator`, `admin` на страницах item/variant и после создания item. Первое изображение в scope автоматически становится primary; если primary удаляется, backend назначает следующим активное изображение по порядку.

После подтверждения upload backend создаёт фоновой задачей оптимизированные WebP-версии:

- `thumbnail` — до 240 px;
- `card` — до 640 px;
- `full` — до 1600 px.

Original сохраняется как есть, derivative-версии не апскейлят маленькие изображения. Обработка снимает EXIF, применяет EXIF orientation, проверяет реальный image payload через Pillow и ограничивает decompression bomb через `Image.MAX_IMAGE_PIXELS`. У media есть `processing_status`: `pending`, `processing`, `ready`, `failed`, а также `processing_error`.

Публичная `primary_image_url` берётся только из `ready` media и предпочитает оптимизированный `card` URL. Если новая primary-картинка ещё `pending` или стала `failed`, старая ready-primary продолжает использоваться публично. Soft delete остаётся на уровне БД; физическое удаление original/derivatives из S3 пока оставлено на будущую lifecycle policy.

Основной сценарий:

1. Пользователь входит.
2. Видит все предметы из своих коллекций.
3. Фильтрует их по коллекции или ищет по названию.
4. Если хочет новый предмет, идёт в каталог.
5. Выбирает предмет по названию и уточняющей строке издания.
6. Добавляет его в коллекцию или wishlist прямо из результатов поиска.
7. Если предмета нет, создаёт заявку.
8. Если заявка была добавлена в wishlist, после approve wishlist автоматически перепривязывается к созданному предмету.

## Тесты

Backend:

```bash
docker compose --profile test up -d db_test
make lint
make typecheck
make test
```

Backend-тесты используют `TEST_DATABASE_URL` и по умолчанию подключаются к отдельной базе:

```text
postgresql+asyncpg://mti:mti@127.0.0.1:5434/mom_this_is_an_investment_test
```

В `backend/tests/conftest.py` есть guard: тесты откажутся запускаться, если имя базы не содержит `test`.

Frontend:

```bash
cd frontend
npm run lint
npm run typecheck
npm run test
npm run build
```

E2E:

```bash
cp .env.example .env
docker compose -p mom-investment-e2e up -d --build db minio minio_init backend frontend
cd frontend
npx playwright install chromium
E2E_BASE_URL=http://localhost:3100 E2E_API_URL=http://localhost:8000/api/v1 npm run test:e2e
cd ..
docker compose -p mom-investment-e2e down -v
```

Playwright покрывает:

- auth redirect и очистку битого JWT;
- role-based навигацию;
- создание коллекции, добавление предмета, update/delete личной записи;
- dynamic reference attributes в каталоге;
- upload изображения и отображение статуса обработки media;
- approve/duplicate/reject заявок через UI модерации;
- перепривязку wishlist после approve.

## Audit и безопасность

Frontend lint переведён с устаревшего `next lint` на `eslint .`.

Текущий `npm audit` после `npm audit fix` остаётся с 5 advisories:

- `esbuild` low, dev-зависимость;
- `js-yaml` через `@redocly/openapi-core`, используется цепочкой генерации OpenAPI типов;
- `postcss` внутри `next`; `npm audit fix --force` предлагает откатить Next до `9.3.3`, поэтому force-fix не применяется.

JWT сейчас хранится в `localStorage`. Клиент очищает токен при `401`, это покрыто unit-тестом, но для production лучше перейти на httpOnly secure cookies, добавить refresh/session rotation, CSRF-модель и rate limiting на login/register.

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
- E2E рассчитаны на seeded dev users и локальный compose-стек.
- Нет Telegram-бота, парсера цен, платежей и marketplace.
- Основной поиск пока SQL-based, без Elasticsearch.
- Rate limiting login пока не внедрён.
