import { expect, test } from "@playwright/test";
import { loginViaUi, logoutViaUi } from "./helpers";

test("protected routes redirect to login and clear an invalid JWT", async ({ page }) => {
  await page.goto("/login");
  await page.evaluate(() => window.localStorage.setItem("mti_access_token", "not-a-valid-token"));

  await page.goto("/collections");

  await expect(page).toHaveURL(/\/login/);
  await expect.poll(() => page.evaluate(() => window.localStorage.getItem("mti_access_token"))).toBeNull();
});

test("sidebar navigation reflects user, moderator and admin roles", async ({ page }) => {
  await loginViaUi(page, "user@example.com");
  await expect(page.getByRole("link", { name: /Модерка/ })).toHaveCount(0);
  await expect(page.getByRole("link", { name: /Админка/ })).toHaveCount(0);
  await logoutViaUi(page);

  await loginViaUi(page, "senior@example.com");
  await expect(page.getByRole("link", { name: /Модерка/ })).toBeVisible();
  await expect(page.getByRole("link", { name: /Админка/ })).toHaveCount(0);
  await logoutViaUi(page);

  await loginViaUi(page, "admin@example.com");
  await expect(page.getByRole("link", { name: /Модерка/ })).toBeVisible();
  await expect(page.getByRole("link", { name: /Админка/ })).toBeVisible();
});
