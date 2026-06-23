PYTHON := backend/venv/bin/python
RUFF := backend/venv/bin/ruff

.PHONY: compose-up compose-down db migrate seed admin lint format typecheck test precommit

compose-up:
	docker compose up -d

compose-down:
	docker compose down

db:
	docker compose up -d db

migrate:
	cd backend && venv/bin/python -m alembic -c alembic.ini upgrade head

seed:
	cd backend && venv/bin/python -m app.scripts.seed_dev

admin:
	cd backend && venv/bin/python -m app.scripts.create_admin

lint:
	$(RUFF) check backend/app backend/alembic backend/tests

format:
	$(RUFF) format backend/app backend/alembic backend/tests

typecheck:
	$(PYTHON) -m mypy backend/app/models backend/app/repositories backend/app/services backend/app/schemas backend/app/api backend/tests backend/app/scripts/create_admin.py backend/app/scripts/seed_dev.py

test:
	$(PYTHON) -m pytest

precommit:
	$(PYTHON) -m pre_commit run --all-files
