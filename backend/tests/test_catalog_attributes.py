from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.models.category import Category
from app.models.user import User

pytestmark = pytest.mark.asyncio


async def test_item_attribute_definition_value_round_trip(
    client: AsyncClient,
    admin: User,
    senior_moderator: User,
    category: Category,
) -> None:
    admin_token = await _login(client, email=admin.email, password="password123")
    senior_token = await _login(client, email=senior_moderator.email, password="password123")
    suffix = uuid4().hex

    attribute_response = await client.post(
        "/api/v1/admin/attributes",
        headers=_auth(admin_token),
        json={
            "category_id": str(category.id),
            "code": f"format_{suffix[:8]}",
            "name": "Format",
            "value_type": "text",
            "is_required": True,
            "is_filterable": True,
            "is_searchable": True,
            "is_variant_attribute": False,
            "sort_order": 10,
        },
    )
    assert attribute_response.status_code == 201
    attribute = attribute_response.json()

    missing_required_response = await client.post(
        "/api/v1/catalog/items",
        headers=_auth(senior_token),
        json={
            "category_id": str(category.id),
            "canonical_title": f"Attribute Missing {suffix}",
            "normalized_title": f"attribute missing {suffix}",
        },
    )
    assert missing_required_response.status_code == 400

    create_response = await client.post(
        "/api/v1/catalog/items",
        headers=_auth(senior_token),
        json={
            "category_id": str(category.id),
            "canonical_title": f"Attribute Item {suffix}",
            "normalized_title": f"attribute item {suffix}",
            "attributes": [
                {
                    "attribute_definition_id": attribute["id"],
                    "value_text": "Hardcover",
                },
            ],
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["attributes"][0]["code"] == attribute["code"]
    assert created["attributes"][0]["display_value"] == "Hardcover"

    get_response = await client.get(f"/api/v1/catalog/items/{created['id']}")
    assert get_response.status_code == 200
    payload = get_response.json()
    assert payload["attributes"][0]["name"] == "Format"
    assert payload["attributes"][0]["value_text"] == "Hardcover"


async def test_reference_attribute_requires_type_and_matching_reference(
    client: AsyncClient,
    admin: User,
    senior_moderator: User,
    category: Category,
) -> None:
    admin_token = await _login(client, email=admin.email, password="password123")
    senior_token = await _login(client, email=senior_moderator.email, password="password123")
    suffix = uuid4().hex[:8]

    missing_type_response = await client.post(
        "/api/v1/admin/attributes",
        headers=_auth(admin_token),
        json={
            "category_id": str(category.id),
            "code": f"publisher_missing_{suffix}",
            "name": "Publisher",
            "value_type": "reference",
            "is_required": True,
        },
    )
    assert missing_type_response.status_code == 422

    publisher_response = await client.post(
        "/api/v1/admin/references",
        headers=_auth(admin_token),
        json={
            "type": "publisher",
            "canonical_name": f"Publisher {suffix}",
            "normalized_name": f"publisher {suffix}",
        },
    )
    assert publisher_response.status_code == 201
    publisher = publisher_response.json()

    manufacturer_response = await client.post(
        "/api/v1/admin/references",
        headers=_auth(admin_token),
        json={
            "type": "manufacturer",
            "canonical_name": f"Manufacturer {suffix}",
            "normalized_name": f"manufacturer {suffix}",
        },
    )
    assert manufacturer_response.status_code == 201
    manufacturer = manufacturer_response.json()

    attribute_response = await client.post(
        "/api/v1/admin/attributes",
        headers=_auth(admin_token),
        json={
            "category_id": str(category.id),
            "code": f"publisher_{suffix}",
            "name": "Publisher",
            "value_type": "reference",
            "reference_type": "publisher",
            "is_required": True,
        },
    )
    assert attribute_response.status_code == 201
    attribute = attribute_response.json()
    assert attribute["reference_type"] == "publisher"
    assert [option["id"] for option in attribute["reference_options"]] == [publisher["id"]]

    list_response = await client.get(
        f"/api/v1/admin/attributes?category_id={category.id}",
        headers=_auth(admin_token),
    )
    assert list_response.status_code == 200
    listed_attribute = next(item for item in list_response.json() if item["id"] == attribute["id"])
    assert listed_attribute["reference_options"][0]["canonical_name"] == publisher["canonical_name"]

    wrong_reference_response = await client.post(
        "/api/v1/catalog/items",
        headers=_auth(senior_token),
        json={
            "category_id": str(category.id),
            "canonical_title": f"Wrong Reference {suffix}",
            "normalized_title": f"wrong reference {suffix}",
            "attributes": [
                {
                    "attribute_definition_id": attribute["id"],
                    "reference_entity_id": manufacturer["id"],
                },
            ],
        },
    )
    assert wrong_reference_response.status_code == 400

    create_response = await client.post(
        "/api/v1/catalog/items",
        headers=_auth(senior_token),
        json={
            "category_id": str(category.id),
            "canonical_title": f"Right Reference {suffix}",
            "normalized_title": f"right reference {suffix}",
            "attributes": [
                {
                    "attribute_definition_id": attribute["id"],
                    "reference_entity_id": publisher["id"],
                },
            ],
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["attributes"][0]["reference_type"] == "publisher"
    assert created["attributes"][0]["reference_label"] == publisher["canonical_name"]
    assert created["attributes"][0]["display_value"] == publisher["canonical_name"]


async def _login(client: AsyncClient, *, email: str, password: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
