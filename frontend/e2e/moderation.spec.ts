import { expect, test } from "@playwright/test";
import {
  createCatalogRequest,
  createCatalogVariant,
  getModerationRequest,
  listWishlist,
  loginApi,
  loginViaUi,
  registerUser,
  uniqueName,
} from "./helpers";

test("senior moderator approves a user request and wishlist is relinked to an active catalog variant", async ({
  page,
  request,
}) => {
  const user = await registerUser(request);
  const userToken = await loginApi(request, user.email);
  const seniorToken = await loginApi(request, "senior@example.com");
  const title = uniqueName("E2E Approve");
  const catalogRequest = await createCatalogRequest(request, userToken, title, { withWishlist: true });

  await loginViaUi(page, "senior@example.com");
  await page.goto(`/moderation/requests/${catalogRequest.id}`);
  await expect(page.getByRole("heading", { name: title })).toBeVisible();
  await page.getByRole("button", { name: "Approve" }).click();
  await expect(page).toHaveURL(/\/moderation\/requests/);

  await expect
    .poll(async () => (await getModerationRequest(request, seniorToken, catalogRequest.id)).status)
    .toBe("approved");
  const approved = await getModerationRequest(request, seniorToken, catalogRequest.id);
  expect(approved.approved_variant_id).toBeTruthy();

  await expect
    .poll(async () => {
      const wishlist = await listWishlist(request, userToken);
      const item = wishlist.find((entry) => entry.catalog_variant_id === approved.approved_variant_id);
      return item?.status;
    })
    .toBe("active");

  const wishlist = await listWishlist(request, userToken);
  const relinked = wishlist.find((entry) => entry.catalog_variant_id === approved.approved_variant_id);
  expect(relinked?.catalog_request_id).toBeNull();
});

test("moderator marks a request as duplicate from the browser", async ({ page, request }) => {
  const user = await registerUser(request);
  const userToken = await loginApi(request, user.email);
  const seniorToken = await loginApi(request, "senior@example.com");
  const variant = await createCatalogVariant(request, seniorToken, uniqueName("E2E Duplicate Target"));
  const catalogRequest = await createCatalogRequest(request, userToken, uniqueName("E2E Duplicate"));

  await loginViaUi(page, "senior@example.com");
  await page.goto(`/moderation/requests/${catalogRequest.id}`);
  await page.getByPlaceholder("existing_variant_id").fill(variant.id);
  await page.getByRole("button", { name: "Duplicate" }).click();
  await expect(page).toHaveURL(/\/moderation\/requests/);

  await expect
    .poll(async () => (await getModerationRequest(request, seniorToken, catalogRequest.id)).status)
    .toBe("duplicate");
});

test("moderator rejects a request with a reason from the browser", async ({ page, request }) => {
  const user = await registerUser(request);
  const userToken = await loginApi(request, user.email);
  const seniorToken = await loginApi(request, "senior@example.com");
  const catalogRequest = await createCatalogRequest(request, userToken, uniqueName("E2E Reject"));

  await loginViaUi(page, "senior@example.com");
  await page.goto(`/moderation/requests/${catalogRequest.id}`);
  await page.getByPlaceholder("Причина отклонения").fill("Not enough identifying information");
  await page.getByRole("button", { name: "Reject" }).click();
  await expect(page).toHaveURL(/\/moderation\/requests/);

  await expect
    .poll(async () => (await getModerationRequest(request, seniorToken, catalogRequest.id)).status)
    .toBe("rejected");
});
