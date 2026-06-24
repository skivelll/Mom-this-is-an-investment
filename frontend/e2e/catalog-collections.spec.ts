import { expect, test } from "@playwright/test";
import {
  createCatalogVariant,
  listCollectionItems,
  listCollections,
  loginApi,
  loginViaUi,
  registerUser,
  uniqueName,
} from "./helpers";

test("user creates a collection, adds a catalog variant, edits and deletes the collection item", async ({
  page,
  request,
}) => {
  const user = await registerUser(request);
  const userToken = await loginApi(request, user.email);
  const seniorToken = await loginApi(request, "senior@example.com");
  const variantTitle = uniqueName("E2E Catalog");
  const variant = await createCatalogVariant(request, seniorToken, variantTitle);
  const collectionName = uniqueName("E2E Shelf");

  await loginViaUi(page, user.email);
  await page.goto("/collections");
  await page.getByPlaceholder("Название коллекции").fill(collectionName);
  await page.getByPlaceholder("Описание").fill("Created from Playwright");
  await page.getByRole("button", { name: "Создать" }).click();
  await expect(page.getByRole("link", { name: new RegExp(collectionName) })).toBeVisible();

  await expect
    .poll(async () => (await listCollections(request, userToken)).some((item) => item.name === collectionName))
    .toBe(true);
  const collection = (await listCollections(request, userToken)).find((item) => item.name === collectionName);
  expect(collection).toBeTruthy();

  await page.goto(`/catalog/variants/${variant.id}`);
  await page.getByRole("combobox").selectOption({ label: collectionName });
  await page.getByRole("button", { name: "В коллекцию" }).click();
  await expect
    .poll(async () => (await listCollectionItems(request, userToken, collection!.id)).length)
    .toBe(1);

  await page.goto(`/collections/${collection!.id}`);
  await expect(page.getByText(`Variant ${variant.id}`)).toBeVisible();
  await page.getByRole("button", { name: "Редактировать" }).click();
  await page.getByLabel("Количество").fill("2");
  await page.getByLabel("Цена").fill("1999");
  await page.getByLabel("Валюта").fill("RUB");
  await page.getByLabel("Комментарий").fill("Edited by Playwright");
  await page.getByRole("button", { name: "Сохранить" }).click();

  await expect(page.getByText("Сохранено")).toBeVisible();
  await expect(page.getByText("Edited by Playwright")).toBeVisible();

  await page.getByRole("button", { name: "Удалить" }).click();
  await expect.poll(async () => (await listCollectionItems(request, userToken, collection!.id)).length).toBe(0);
});
