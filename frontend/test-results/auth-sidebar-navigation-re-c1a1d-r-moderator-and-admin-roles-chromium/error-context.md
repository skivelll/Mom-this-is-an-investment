# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth.spec.ts >> sidebar navigation reflects user, moderator and admin roles
- Location: e2e/auth.spec.ts:14:5

# Error details

```
Error: locator.fill: Test ended.
Call log:
  - waiting for getByLabel('Пароль')

```

# Test source

```ts
  1   | import { expect, type APIRequestContext, type Page } from "@playwright/test";
  2   | 
  3   | export const API_URL = process.env.E2E_API_URL ?? "http://localhost:8000/api/v1";
  4   | export const DEV_PASSWORD = "password123";
  5   | 
  6   | type TokenResponse = { access_token: string };
  7   | type Category = { id: string; slug: string };
  8   | type AttributeDefinition = {
  9   |   id: string;
  10  |   value_type: "text" | "integer" | "decimal" | "boolean" | "date" | "reference";
  11  |   is_required: boolean;
  12  |   is_variant_attribute: boolean;
  13  |   reference_options: ReferenceEntity[];
  14  | };
  15  | type ReferenceEntity = { id: string };
  16  | type Collection = { id: string; name: string };
  17  | type CollectionItem = { id: string; comment: string | null };
  18  | type CatalogVariant = { id: string; catalog_item_id: string };
  19  | type CatalogRequest = { id: string; status: string; approved_variant_id: string | null };
  20  | type WishlistItem = {
  21  |   catalog_request_id: string | null;
  22  |   catalog_variant_id: string | null;
  23  |   status: string;
  24  | };
  25  | 
  26  | export function uniqueName(prefix: string) {
  27  |   return `${prefix} ${Date.now()} ${Math.random().toString(16).slice(2)}`;
  28  | }
  29  | 
  30  | export async function registerUser(api: APIRequestContext) {
  31  |   const suffix = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  32  |   const user = {
  33  |     username: `e2e-${suffix}`,
  34  |     email: `e2e-${suffix}@example.com`,
  35  |     password: DEV_PASSWORD,
  36  |   };
  37  |   const response = await api.post(`${API_URL}/auth/register`, { data: user });
  38  |   expect(response.ok()).toBeTruthy();
  39  |   return user;
  40  | }
  41  | 
  42  | export async function loginApi(api: APIRequestContext, email: string, password = DEV_PASSWORD) {
  43  |   const response = await api.post(`${API_URL}/auth/login`, {
  44  |     data: { email, password },
  45  |   });
  46  |   expect(response.ok()).toBeTruthy();
  47  |   const body = (await response.json()) as TokenResponse;
  48  |   return body.access_token;
  49  | }
  50  | 
  51  | export async function loginViaUi(page: Page, email: string, password = DEV_PASSWORD) {
  52  |   await page.goto("/login");
  53  |   await page.getByLabel("Email").fill(email);
> 54  |   await page.getByLabel("Пароль").fill(password);
      |                                   ^ Error: locator.fill: Test ended.
  55  |   await page.getByRole("button", { name: "Войти" }).click();
  56  |   await expect(page).toHaveURL(/\/dashboard/);
  57  | }
  58  | 
  59  | export async function logoutViaUi(page: Page) {
  60  |   await page.getByRole("button", { name: "Выйти" }).click();
  61  |   await expect(page).toHaveURL(/\/login/);
  62  | }
  63  | 
  64  | export async function getCategory(api: APIRequestContext, slug = "comics") {
  65  |   const response = await api.get(`${API_URL}/admin/categories`);
  66  |   expect(response.ok()).toBeTruthy();
  67  |   const categories = (await response.json()) as Category[];
  68  |   const category = categories.find((item) => item.slug === slug);
  69  |   expect(category).toBeTruthy();
  70  |   return category as Category;
  71  | }
  72  | 
  73  | export async function createCatalogVariant(api: APIRequestContext, token: string, title: string) {
  74  |   const category = await getCategory(api);
  75  |   const attributes = await getAttributes(api, category.id);
  76  |   const itemResponse = await api.post(`${API_URL}/catalog/items`, {
  77  |     headers: authHeaders(token),
  78  |     data: {
  79  |       category_id: category.id,
  80  |       canonical_title: title,
  81  |       normalized_title: title.toLowerCase(),
  82  |       status: "active",
  83  |       attributes: requiredAttributeValues(attributes.filter((attribute) => !attribute.is_variant_attribute)),
  84  |     },
  85  |   });
  86  |   expect(itemResponse.ok()).toBeTruthy();
  87  |   const item = (await itemResponse.json()) as { id: string };
  88  | 
  89  |   const variantResponse = await api.post(`${API_URL}/catalog/variants`, {
  90  |     headers: authHeaders(token),
  91  |     data: {
  92  |       catalog_item_id: item.id,
  93  |       canonical_title: `${title} Variant`,
  94  |       normalized_title: `${title.toLowerCase()} variant`,
  95  |       sku: `E2E-${Date.now()}`,
  96  |       status: "active",
  97  |       attributes: requiredAttributeValues(attributes.filter((attribute) => attribute.is_variant_attribute)),
  98  |     },
  99  |   });
  100 |   expect(variantResponse.ok()).toBeTruthy();
  101 |   return (await variantResponse.json()) as CatalogVariant;
  102 | }
  103 | 
  104 | async function getAttributes(api: APIRequestContext, categoryId: string) {
  105 |   const response = await api.get(`${API_URL}/admin/attributes?category_id=${categoryId}`);
  106 |   expect(response.ok()).toBeTruthy();
  107 |   return (await response.json()) as AttributeDefinition[];
  108 | }
  109 | 
  110 | function requiredAttributeValues(attributes: AttributeDefinition[]) {
  111 |   return attributes
  112 |     .filter((attribute) => attribute.is_required)
  113 |     .map((attribute) => {
  114 |       const base = { attribute_definition_id: attribute.id };
  115 |       if (attribute.value_type === "text") return { ...base, value_text: "E2E value" };
  116 |       if (attribute.value_type === "integer") return { ...base, value_integer: 1 };
  117 |       if (attribute.value_type === "decimal") return { ...base, value_decimal: "1.00" };
  118 |       if (attribute.value_type === "boolean") return { ...base, value_boolean: true };
  119 |       if (attribute.value_type === "date") return { ...base, value_date: "2026-01-01" };
  120 |       if (attribute.value_type === "reference") {
  121 |         const reference = attribute.reference_options[0];
  122 |         expect(reference).toBeTruthy();
  123 |         return { ...base, reference_entity_id: reference.id };
  124 |       }
  125 |       return base;
  126 |     });
  127 | }
  128 | 
  129 | export async function createCatalogRequest(
  130 |   api: APIRequestContext,
  131 |   token: string,
  132 |   title: string,
  133 |   options: { withWishlist?: boolean } = {},
  134 | ) {
  135 |   const category = await getCategory(api);
  136 |   const response = await api.post(`${API_URL}/catalog-requests`, {
  137 |     headers: authHeaders(token),
  138 |     data: {
  139 |       category_id: category.id,
  140 |       raw_title: title,
  141 |       description: "Created by Playwright",
  142 |       proposed_data: {},
  143 |       wishlist: options.withWishlist
  144 |         ? {
  145 |             target_price: 1500,
  146 |             currency: "RUB",
  147 |             priority: 10,
  148 |             comment: "Track this after moderation",
  149 |           }
  150 |         : undefined,
  151 |     },
  152 |   });
  153 |   expect(response.ok()).toBeTruthy();
  154 |   return ((await response.json()) as { request: CatalogRequest }).request;
```