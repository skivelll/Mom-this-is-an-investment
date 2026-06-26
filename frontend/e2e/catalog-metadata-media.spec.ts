import { expect, test } from "@playwright/test";
import { createCatalogVariant, loginApi, loginViaUi, uniqueName } from "./helpers";

const tinyPng = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAFgwJ/lI2oWQAAAABJRU5ErkJggg==",
  "base64",
);

test("catalog dynamic reference attributes show only matching reference options", async ({ page }) => {
  await loginViaUi(page, "senior@example.com");
  await page.goto("/catalog");

  await page.locator("form").first().locator("select").first().selectOption({ label: "Comics" });

  const publisherSelect = page.getByLabel(/Publisher/);
  await expect(publisherSelect).toBeVisible();
  await expect(publisherSelect).toContainText("Marvel Comics");
  await expect(publisherSelect).not.toContainText("Good Smile Company");
});

test("moderator uploads catalog media and sees processing status", async ({ page, request }) => {
  const seniorToken = await loginApi(request, "senior@example.com");
  const variant = await createCatalogVariant(request, seniorToken, uniqueName("E2E Media"));

  await loginViaUi(page, "senior@example.com");
  await page.goto(`/catalog/variants/${variant.id}`);
  await page.locator('input[type="file"]').setInputFiles({
    name: "cover.png",
    mimeType: "image/png",
    buffer: tinyPng,
  });
  await page.getByRole("button", { name: "Загрузить" }).click();

  await expect(page.getByText(/Обрабатывается|Готово/)).toBeVisible();
  await expect(page.getByText("Готово")).toBeVisible({ timeout: 15_000 });
});
