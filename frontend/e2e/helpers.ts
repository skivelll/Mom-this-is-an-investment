import { expect, type APIRequestContext, type Page } from "@playwright/test";

export const API_URL = process.env.E2E_API_URL ?? "http://localhost:8000/api/v1";
export const DEV_PASSWORD = "password123";

type TokenResponse = { access_token: string };
type Category = { id: string; slug: string };
type Collection = { id: string; name: string };
type CollectionItem = { id: string; comment: string | null };
type CatalogVariant = { id: string; catalog_item_id: string };
type CatalogRequest = { id: string; status: string; approved_variant_id: string | null };
type WishlistItem = {
  catalog_request_id: string | null;
  catalog_variant_id: string | null;
  status: string;
};

export function uniqueName(prefix: string) {
  return `${prefix} ${Date.now()} ${Math.random().toString(16).slice(2)}`;
}

export async function registerUser(api: APIRequestContext) {
  const suffix = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const user = {
    username: `e2e-${suffix}`,
    email: `e2e-${suffix}@example.com`,
    password: DEV_PASSWORD,
  };
  const response = await api.post(`${API_URL}/auth/register`, { data: user });
  expect(response.ok()).toBeTruthy();
  return user;
}

export async function loginApi(api: APIRequestContext, email: string, password = DEV_PASSWORD) {
  const response = await api.post(`${API_URL}/auth/login`, {
    data: { email, password },
  });
  expect(response.ok()).toBeTruthy();
  const body = (await response.json()) as TokenResponse;
  return body.access_token;
}

export async function loginViaUi(page: Page, email: string, password = DEV_PASSWORD) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Пароль").fill(password);
  await page.getByRole("button", { name: "Войти" }).click();
  await expect(page).toHaveURL(/\/dashboard/);
}

export async function logoutViaUi(page: Page) {
  await page.getByRole("button", { name: "Выйти" }).click();
  await expect(page).toHaveURL(/\/login/);
}

export async function getCategory(api: APIRequestContext, slug = "comics") {
  const response = await api.get(`${API_URL}/admin/categories`);
  expect(response.ok()).toBeTruthy();
  const categories = (await response.json()) as Category[];
  const category = categories.find((item) => item.slug === slug);
  expect(category).toBeTruthy();
  return category as Category;
}

export async function createCatalogVariant(api: APIRequestContext, token: string, title: string) {
  const category = await getCategory(api);
  const itemResponse = await api.post(`${API_URL}/catalog/items`, {
    headers: authHeaders(token),
    data: {
      category_id: category.id,
      canonical_title: title,
      normalized_title: title.toLowerCase(),
      status: "active",
    },
  });
  expect(itemResponse.ok()).toBeTruthy();
  const item = (await itemResponse.json()) as { id: string };

  const variantResponse = await api.post(`${API_URL}/catalog/variants`, {
    headers: authHeaders(token),
    data: {
      catalog_item_id: item.id,
      canonical_title: `${title} Variant`,
      normalized_title: `${title.toLowerCase()} variant`,
      sku: `E2E-${Date.now()}`,
      status: "active",
    },
  });
  expect(variantResponse.ok()).toBeTruthy();
  return (await variantResponse.json()) as CatalogVariant;
}

export async function createCatalogRequest(
  api: APIRequestContext,
  token: string,
  title: string,
  options: { withWishlist?: boolean } = {},
) {
  const category = await getCategory(api);
  const response = await api.post(`${API_URL}/catalog-requests`, {
    headers: authHeaders(token),
    data: {
      category_id: category.id,
      raw_title: title,
      description: "Created by Playwright",
      proposed_data: {},
      wishlist: options.withWishlist
        ? {
            target_price: 1500,
            currency: "RUB",
            priority: 10,
            comment: "Track this after moderation",
          }
        : undefined,
    },
  });
  expect(response.ok()).toBeTruthy();
  return ((await response.json()) as { request: CatalogRequest }).request;
}

export async function getModerationRequest(api: APIRequestContext, token: string, requestId: string) {
  const response = await api.get(`${API_URL}/moderation/catalog-requests/${requestId}`, {
    headers: authHeaders(token),
  });
  expect(response.ok()).toBeTruthy();
  return (await response.json()) as CatalogRequest;
}

export async function listWishlist(api: APIRequestContext, token: string) {
  const response = await api.get(`${API_URL}/wishlist`, { headers: authHeaders(token) });
  expect(response.ok()).toBeTruthy();
  return (await response.json()) as WishlistItem[];
}

export async function listCollections(api: APIRequestContext, token: string) {
  const response = await api.get(`${API_URL}/collections`, { headers: authHeaders(token) });
  expect(response.ok()).toBeTruthy();
  return (await response.json()) as Collection[];
}

export async function listCollectionItems(api: APIRequestContext, token: string, collectionId: string) {
  const response = await api.get(`${API_URL}/collections/${collectionId}/items`, {
    headers: authHeaders(token),
  });
  expect(response.ok()).toBeTruthy();
  return (await response.json()) as CollectionItem[];
}

export function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}
