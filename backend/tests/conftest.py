from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from alembic import command
from app.api.dependencies import get_current_user
from app.core.security import hash_password
from app.db.session import get_db_session
from app.main import app
from app.models.category import Category
from app.models.collections import Collection, CollectionItem, CollectionVisibility, ItemCondition
from app.models.item import CatalogItem, CatalogStatus
from app.models.user import User, UserRole
from app.models.variant import CatalogVariant

DEFAULT_TEST_DATABASE_URL = (
    "postgresql+asyncpg://mti:mti@127.0.0.1:5434/mom_this_is_an_investment_test"
)


@dataclass(slots=True)
class TestData:
    user: User
    moderator: User
    senior_moderator: User
    admin: User
    category: Category
    catalog_item: CatalogItem
    catalog_variant: CatalogVariant
    collection: Collection
    collection_item: CollectionItem


def pytest_configure(config: pytest.Config) -> None:
    _ = config
    _assert_safe_test_database_url(_test_database_url())


@pytest.fixture(scope="session")
def test_database_url() -> str:
    return _test_database_url()


@pytest_asyncio.fixture(scope="session")
async def test_engine(test_database_url: str) -> AsyncGenerator[AsyncEngine]:
    await _ensure_database_exists(test_database_url)
    await asyncio.to_thread(_run_migrations, test_database_url)
    engine = create_async_engine(test_database_url)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession]:
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        test_session_factory = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        async def override_get_db_session() -> AsyncGenerator[AsyncSession]:
            async with test_session_factory() as session:
                yield session

        app.dependency_overrides[get_db_session] = override_get_db_session

        async with test_session_factory() as session:
            try:
                yield session
            finally:
                await session.close()
                app.dependency_overrides.pop(get_db_session, None)
                app.dependency_overrides.pop(get_current_user, None)
                await transaction.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    _ = db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest_asyncio.fixture
async def test_data(db_session: AsyncSession) -> TestData:
    suffix = uuid4().hex
    password = "password123"
    user = User(
        email=f"user-{suffix}@example.com",
        username=f"user-{suffix}",
        password_hash=hash_password(password),
        role=UserRole.USER,
        is_active=True,
    )
    moderator = User(
        email=f"moderator-{suffix}@example.com",
        username=f"moderator-{suffix}",
        password_hash=hash_password(password),
        role=UserRole.MODERATOR,
        is_active=True,
    )
    senior = User(
        email=f"senior-{suffix}@example.com",
        username=f"senior-{suffix}",
        password_hash=hash_password(password),
        role=UserRole.SENIOR_MODERATOR,
        is_active=True,
    )
    admin = User(
        email=f"admin-{suffix}@example.com",
        username=f"admin-{suffix}",
        password_hash=hash_password(password),
        role=UserRole.ADMIN,
        is_active=True,
    )
    category = Category(
        name=f"Figures {suffix}",
        slug=f"figures-{suffix}",
        description="Test category",
        is_active=True,
    )
    db_session.add_all([user, moderator, senior, admin, category])
    await db_session.flush()

    item = CatalogItem(
        category_id=category.id,
        canonical_title=f"Test Item {suffix}",
        normalized_title=f"test item {suffix}",
        status=CatalogStatus.ACTIVE,
        created_by_id=senior.id,
    )
    db_session.add(item)
    await db_session.flush()

    variant = CatalogVariant(
        catalog_item_id=item.id,
        canonical_title=f"Test Variant {suffix}",
        normalized_title=f"test variant {suffix}",
        sku=f"TEST-{suffix}",
        status=CatalogStatus.ACTIVE,
        created_by_id=senior.id,
    )
    collection = Collection(
        owner_id=user.id,
        name=f"Collection {suffix}",
        description="Test collection",
        visibility=CollectionVisibility.PRIVATE,
    )
    db_session.add_all([variant, collection])
    await db_session.flush()

    collection_item = CollectionItem(
        collection_id=collection.id,
        catalog_variant_id=variant.id,
        condition=ItemCondition.NEW,
        quantity=1,
        purchase_price=None,
        purchase_currency=None,
        purchase_date=None,
        comment="Original comment",
    )
    db_session.add(collection_item)
    await db_session.flush()

    return TestData(
        user=user,
        moderator=moderator,
        senior_moderator=senior,
        admin=admin,
        category=category,
        catalog_item=item,
        catalog_variant=variant,
        collection=collection,
        collection_item=collection_item,
    )


@pytest.fixture
def user(test_data: TestData) -> User:
    return test_data.user


@pytest.fixture
def moderator(test_data: TestData) -> User:
    return test_data.moderator


@pytest.fixture
def senior_moderator(test_data: TestData) -> User:
    return test_data.senior_moderator


@pytest.fixture
def admin(test_data: TestData) -> User:
    return test_data.admin


@pytest.fixture
def category(test_data: TestData) -> Category:
    return test_data.category


@pytest.fixture
def catalog_item(test_data: TestData) -> CatalogItem:
    return test_data.catalog_item


@pytest.fixture
def catalog_variant(test_data: TestData) -> CatalogVariant:
    return test_data.catalog_variant


@pytest.fixture
def collection(test_data: TestData) -> Collection:
    return test_data.collection


@pytest.fixture
def collection_item(test_data: TestData) -> CollectionItem:
    return test_data.collection_item


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _test_database_url() -> str:
    return os.getenv("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)


def _assert_safe_test_database_url(database_url: str) -> None:
    url = make_url(database_url)
    database_name = url.database or ""
    if "test" not in database_name.lower():
        raise RuntimeError(
            "Refusing to run tests: TEST_DATABASE_URL database name must contain 'test'. "
            f"Current database is {database_name!r}."
        )


async def _ensure_database_exists(database_url: str) -> None:
    url = make_url(database_url)
    database_name = url.database
    if database_name is None:
        raise RuntimeError("TEST_DATABASE_URL must include a database name.")

    admin_url = url.set(database="postgres")
    admin_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        async with admin_engine.connect() as connection:
            exists = await connection.scalar(
                text("select 1 from pg_database where datname = :database_name"),
                {"database_name": database_name},
            )
            if exists is None:
                await connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    finally:
        await admin_engine.dispose()


def _run_migrations(database_url: str) -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    previous_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    try:
        command.upgrade(alembic_cfg, "head")
    finally:
        if previous_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_url
