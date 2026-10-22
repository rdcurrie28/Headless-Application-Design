import { test, expect } from "./fixtures";

test("at-risk watchlist lists churn risks, highest first", async ({ page }) => {
  await page.goto("/watchlists/at-risk");
  await expect(page.getByRole("heading", { level: 1, name: "At-risk watchlist" })).toBeVisible();
  const links = page.getByRole("grid", { name: "At-risk watchlist" }).locator("tbody tr td:first-child a");
  await expect(links).toHaveText(["Evergreen Retail", "Blue Ridge Health"]);
  await expect(page.getByText("Usage decline 60d").first()).toBeVisible();
});

test("expansion targets list, highest first", async ({ page }) => {
  await page.goto("/watchlists/expansion");
  await expect(page.getByRole("heading", { level: 1, name: "Expansion targets" })).toBeVisible();
  const links = page.getByRole("grid", { name: "Expansion targets" }).locator("tbody tr td:first-child a");
  await expect(links).toHaveText(["Cardinal Logistics", "Acme Aerospace", "Delta Fintech"]);
});

test("owner filter narrows the watchlist", async ({ page }) => {
  await page.goto("/watchlists/expansion");
  await page.getByRole("textbox", { name: "Filter by owner" }).fill("jlee");
  const links = page.getByRole("grid", { name: "Expansion targets" }).locator("tbody tr td:first-child a");
  await expect(links).toHaveText(["Cardinal Logistics", "Acme Aerospace"]);
});

test("owner filter with no matches shows the empty state", async ({ page }) => {
  await page.goto("/watchlists/at-risk");
  await page.getByRole("textbox", { name: "Filter by owner" }).fill("nobody");
  await expect(page.getByRole("heading", { name: "Nothing to act on" })).toBeVisible();
});

test("watchlist row opens the account", async ({ page }) => {
  await page.goto("/watchlists/at-risk");
  await page.getByRole("link", { name: "Blue Ridge Health" }).click();
  await expect(page).toHaveURL(/\/accounts\/C-1002$/);
  await expect(page.getByRole("heading", { level: 1, name: "Blue Ridge Health" })).toBeVisible();
});
