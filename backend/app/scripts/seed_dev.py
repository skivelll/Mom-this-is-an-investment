from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.category import AttributeDefinition, AttributeValueType, Category
from app.models.collections import Collection, CollectionItem, CollectionVisibility, ItemCondition
from app.models.item import CatalogItem, CatalogStatus
from app.models.reference import ReferenceEntity, ReferenceType
from app.models.request import CatalogRequest, CatalogRequestStatus
from app.models.user import User, UserRole
from app.models.variant import CatalogVariant
from app.models.wishlist import WishlistItem, WishlistStatus

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
    UserSeed("moderator@example.com", "moderator", UserRole.MODERATOR),
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


async def seed_catalog(
    session: AsyncSession,
    *,
    categories: dict[str, Category],
    senior: User,
) -> tuple[CatalogItem, CatalogVariant]:
    item = await session.scalar(
        select(CatalogItem).where(
            CatalogItem.normalized_title == "absolute spider man",
            CatalogItem.category_id == categories["comics"].id,
        ),
    )
    if item is None:
        item = CatalogItem(
            category_id=categories["comics"].id,
            canonical_title="Absolute Spider-Man",
            normalized_title="absolute spider man",
            description="Dev seed comic series for local catalog testing.",
            release_year=2024,
            status=CatalogStatus.ACTIVE,
            created_by_id=senior.id,
        )
        session.add(item)
        await session.flush()
    else:
        item.canonical_title = "Absolute Spider-Man"
        item.description = "Dev seed comic series for local catalog testing."
        item.release_year = 2024
        item.status = CatalogStatus.ACTIVE

    variant = await session.scalar(
        select(CatalogVariant).where(CatalogVariant.sku == "DEV-ASM-001"),
    )
    if variant is None:
        variant = CatalogVariant(
            catalog_item_id=item.id,
            canonical_title="Absolute Spider-Man #1 A Cover",
            normalized_title="absolute spider man 1 a cover",
            sku="DEV-ASM-001",
            barcode="978000000001",
            release_date=date(2024, 1, 10),
            status=CatalogStatus.ACTIVE,
            created_by_id=senior.id,
        )
        session.add(variant)
        await session.flush()
    else:
        variant.catalog_item_id = item.id
        variant.canonical_title = "Absolute Spider-Man #1 A Cover"
        variant.normalized_title = "absolute spider man 1 a cover"
        variant.barcode = "978000000001"
        variant.release_date = date(2024, 1, 10)
        variant.status = CatalogStatus.ACTIVE

    second_variant = await session.scalar(
        select(CatalogVariant).where(CatalogVariant.sku == "DEV-ASM-001-VIRGIN"),
    )
    if second_variant is None:
        session.add(
            CatalogVariant(
                catalog_item_id=item.id,
                canonical_title="Absolute Spider-Man #1 Virgin Variant",
                normalized_title="absolute spider man 1 virgin variant",
                sku="DEV-ASM-001-VIRGIN",
                barcode="978000000002",
                release_date=date(2024, 1, 10),
                status=CatalogStatus.ACTIVE,
                created_by_id=senior.id,
            ),
        )

    return item, variant


async def seed_user_shelf(
    session: AsyncSession,
    *,
    user: User,
    variant: CatalogVariant,
) -> None:
    collection = await session.scalar(
        select(Collection).where(
            Collection.owner_id == user.id,
            Collection.name == "Dev shelf",
        ),
    )
    if collection is None:
        collection = Collection(
            owner_id=user.id,
            name="Dev shelf",
            description="Local development collection.",
            visibility=CollectionVisibility.PRIVATE,
        )
        session.add(collection)
        await session.flush()

    collection_item = await session.scalar(
        select(CollectionItem).where(
            CollectionItem.collection_id == collection.id,
            CollectionItem.catalog_variant_id == variant.id,
        ),
    )
    if collection_item is None:
        session.add(
            CollectionItem(
                collection_id=collection.id,
                catalog_variant_id=variant.id,
                condition=ItemCondition.NEW,
                quantity=1,
                purchase_price=Decimal("12.99"),
                purchase_currency="USD",
                purchase_date=date(2024, 2, 1),
                comment="Seeded collection item.",
            ),
        )

    wishlist_item = await session.scalar(
        select(WishlistItem).where(
            WishlistItem.user_id == user.id,
            WishlistItem.catalog_variant_id == variant.id,
        ),
    )
    if wishlist_item is None:
        session.add(
            WishlistItem(
                user_id=user.id,
                catalog_variant_id=variant.id,
                catalog_request_id=None,
                target_price=Decimal("10.00"),
                currency="USD",
                source_url=None,
                priority=20,
                status=WishlistStatus.ACTIVE,
                comment="Seeded wishlist item.",
            ),
        )


async def seed_pending_request(
    session: AsyncSession,
    *,
    categories: dict[str, Category],
    user: User,
) -> None:
    request = await session.scalar(
        select(CatalogRequest).where(
            CatalogRequest.created_by_id == user.id,
            CatalogRequest.raw_title == "Null Point GPX #1",
        ),
    )
    if request is None:
        request = CatalogRequest(
            created_by_id=user.id,
            category_id=categories["comics"].id,
            raw_title="Null Point GPX #1",
            description="Pending seed request for moderation flow.",
            source_url="https://example.com/null-point-gpx-1",
            proposed_data={"issue_number": "1", "publisher": "Null Point"},
            status=CatalogRequestStatus.PENDING,
        )
        session.add(request)
        await session.flush()

    pending_wishlist = await session.scalar(
        select(WishlistItem).where(
            WishlistItem.user_id == user.id,
            WishlistItem.catalog_request_id == request.id,
        ),
    )
    if pending_wishlist is None and request.status == CatalogRequestStatus.PENDING:
        session.add(
            WishlistItem(
                user_id=user.id,
                catalog_variant_id=None,
                catalog_request_id=request.id,
                target_price=Decimal("25.00"),
                currency="USD",
                source_url="https://example.com/null-point-gpx-1",
                priority=50,
                status=WishlistStatus.PENDING_MODERATION,
                comment="Seeded pending wishlist item.",
            ),
        )


async def seed_dev_data(session: AsyncSession) -> None:
    async with session.begin():
        await seed_users(session)
        categories = await seed_categories(session)
        await seed_attributes(session, categories)
        await seed_references(session)
        user = await session.scalar(select(User).where(User.email == "user@example.com"))
        senior = await session.scalar(select(User).where(User.email == "senior@example.com"))
        if user is None or senior is None:
            raise RuntimeError("Seed users were not created.")
        _, variant = await seed_catalog(session, categories=categories, senior=senior)
        await seed_user_shelf(session, user=user, variant=variant)
        await seed_pending_request(session, categories=categories, user=user)


async def _async_main() -> int:
    async with SessionLocal() as session:
        await seed_dev_data(session)
    print("Dev seed data has been applied.")
    return 0


def main() -> int:
    return asyncio.run(_async_main())


if __name__ == "__main__":
    raise SystemExit(main())
