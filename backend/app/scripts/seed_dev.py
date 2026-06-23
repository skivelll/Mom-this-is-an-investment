from __future__ import annotations

import asyncio
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.category import AttributeDefinition, AttributeValueType, Category
from app.models.reference import ReferenceEntity, ReferenceType
from app.models.user import User, UserRole

DEV_PASSWORD = "password123"


@dataclass(frozen=True, slots=True)
class UserSeed:
    email: str
    username: str
    role: UserRole


@dataclass(frozen=True, slots=True)
class CategorySeed:
    name: str
    slug: str
    description: str


@dataclass(frozen=True, slots=True)
class AttributeSeed:
    category_slug: str
    code: str
    name: str
    value_type: AttributeValueType
    is_required: bool = False
    is_filterable: bool = False
    is_searchable: bool = False
    is_variant_attribute: bool = False
    sort_order: int = 0


@dataclass(frozen=True, slots=True)
class ReferenceSeed:
    type: ReferenceType
    canonical_name: str
    normalized_name: str


USERS = [
    UserSeed("admin@example.com", "admin", UserRole.ADMIN),
    UserSeed("senior@example.com", "senior-moderator", UserRole.SENIOR_MODERATOR),
    UserSeed("user@example.com", "demo-user", UserRole.USER),
]

CATEGORIES = [
    CategorySeed("Comics", "comics", "Комиксы и одиночные выпуски."),
    CategorySeed("Manga", "manga", "Манга и ранобэ-серии."),
    CategorySeed("Books", "books", "Книги, артбуки и энциклопедии."),
    CategorySeed("Figures", "figures", "Фигурки, статуэтки и виниловые коллекционные предметы."),
    CategorySeed("Cards", "cards", "Коллекционные карточки и наборы карточек."),
]

ATTRIBUTES = [
    AttributeSeed(
        "figures",
        "manufacturer",
        "Manufacturer",
        AttributeValueType.REFERENCE,
        True,
        True,
        True,
    ),
    AttributeSeed(
        "figures",
        "franchise",
        "Franchise",
        AttributeValueType.REFERENCE,
        False,
        True,
        True,
    ),
    AttributeSeed(
        "figures",
        "character",
        "Character",
        AttributeValueType.REFERENCE,
        False,
        True,
        True,
    ),
    AttributeSeed("figures", "series", "Series", AttributeValueType.REFERENCE, False, True, True),
    AttributeSeed(
        "figures", "series_number", "Series number", AttributeValueType.TEXT, False, True
    ),
    AttributeSeed(
        "figures", "variant", "Variant", AttributeValueType.TEXT, False, True, True, True
    ),
    AttributeSeed(
        "comics", "publisher", "Publisher", AttributeValueType.REFERENCE, True, True, True
    ),
    AttributeSeed("comics", "series", "Series", AttributeValueType.REFERENCE, True, True, True),
    AttributeSeed("comics", "issue_number", "Issue number", AttributeValueType.TEXT, True, True),
    AttributeSeed("comics", "writer", "Writer", AttributeValueType.REFERENCE, False, True, True),
    AttributeSeed("comics", "artist", "Artist", AttributeValueType.REFERENCE, False, True, True),
    AttributeSeed(
        "manga",
        "publisher",
        "Publisher",
        AttributeValueType.REFERENCE,
        False,
        True,
        True,
    ),
    AttributeSeed("manga", "series", "Series", AttributeValueType.REFERENCE, True, True, True),
    AttributeSeed("manga", "volume", "Volume", AttributeValueType.INTEGER, False, True),
    AttributeSeed("books", "author", "Author", AttributeValueType.REFERENCE, False, True, True),
    AttributeSeed(
        "books",
        "publisher",
        "Publisher",
        AttributeValueType.REFERENCE,
        False,
        True,
        True,
    ),
    AttributeSeed("cards", "series", "Series", AttributeValueType.REFERENCE, False, True, True),
    AttributeSeed("cards", "card_number", "Card number", AttributeValueType.TEXT, False, True),
]

REFERENCES = [
    ReferenceSeed(ReferenceType.MANUFACTURER, "Good Smile Company", "good smile company"),
    ReferenceSeed(ReferenceType.PUBLISHER, "Marvel Comics", "marvel comics"),
    ReferenceSeed(ReferenceType.FRANCHISE, "Spider-Man", "spider man"),
    ReferenceSeed(ReferenceType.CHARACTER, "Spider-Man", "spider man"),
    ReferenceSeed(ReferenceType.AUTHOR, "Stan Lee", "stan lee"),
    ReferenceSeed(ReferenceType.SERIES, "Amazing Spider-Man", "amazing spider man"),
]


async def seed_users(session: AsyncSession) -> None:
    for seed in USERS:
        user = await session.scalar(select(User).where(User.email == seed.email))
        if user is None:
            session.add(
                User(
                    email=seed.email,
                    username=seed.username,
                    password_hash=hash_password(DEV_PASSWORD),
                    role=seed.role,
                    is_active=True,
                ),
            )
        else:
            user.username = seed.username
            user.password_hash = hash_password(DEV_PASSWORD)
            user.role = seed.role
            user.is_active = True


async def seed_categories(session: AsyncSession) -> dict[str, Category]:
    categories: dict[str, Category] = {}
    for seed in CATEGORIES:
        category = await session.scalar(select(Category).where(Category.slug == seed.slug))
        if category is None:
            category = Category(
                name=seed.name,
                slug=seed.slug,
                description=seed.description,
                is_active=True,
            )
            session.add(category)
            await session.flush()
        else:
            category.name = seed.name
            category.description = seed.description
            category.is_active = True
        categories[seed.slug] = category
    return categories


async def seed_attributes(session: AsyncSession, categories: dict[str, Category]) -> None:
    for seed in ATTRIBUTES:
        category = categories[seed.category_slug]
        definition = await session.scalar(
            select(AttributeDefinition).where(
                AttributeDefinition.category_id == category.id,
                AttributeDefinition.code == seed.code,
            ),
        )
        if definition is None:
            session.add(
                AttributeDefinition(
                    category_id=category.id,
                    code=seed.code,
                    name=seed.name,
                    value_type=seed.value_type,
                    is_required=seed.is_required,
                    is_filterable=seed.is_filterable,
                    is_searchable=seed.is_searchable,
                    is_variant_attribute=seed.is_variant_attribute,
                    sort_order=seed.sort_order,
                    validation_rules=None,
                ),
            )
        else:
            definition.name = seed.name
            definition.value_type = seed.value_type
            definition.is_required = seed.is_required
            definition.is_filterable = seed.is_filterable
            definition.is_searchable = seed.is_searchable
            definition.is_variant_attribute = seed.is_variant_attribute
            definition.sort_order = seed.sort_order


async def seed_references(session: AsyncSession) -> None:
    for seed in REFERENCES:
        reference = await session.scalar(
            select(ReferenceEntity).where(
                ReferenceEntity.type == seed.type,
                ReferenceEntity.normalized_name == seed.normalized_name,
            ),
        )
        if reference is None:
            session.add(
                ReferenceEntity(
                    type=seed.type,
                    canonical_name=seed.canonical_name,
                    normalized_name=seed.normalized_name,
                ),
            )
        else:
            reference.canonical_name = seed.canonical_name


async def seed_dev_data(session: AsyncSession) -> None:
    async with session.begin():
        await seed_users(session)
        categories = await seed_categories(session)
        await seed_attributes(session, categories)
        await seed_references(session)


async def _async_main() -> int:
    async with SessionLocal() as session:
        await seed_dev_data(session)
    print("Dev seed data has been applied.")
    return 0


def main() -> int:
    return asyncio.run(_async_main())


if __name__ == "__main__":
    raise SystemExit(main())
