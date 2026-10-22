import { test, expect } from "./fixtures";

const ALL = ["Acme Aerospace", "Blue Ridge Health", "Cardinal Logistics", "Delta Fintech", "Evergreen Retail"];

test.beforeEach(async ({ page }) => {
  await page.goto("/");
});

test("root redirects to accounts and lists every customer", async ({ page }) => {
  await expect(page).toHaveURL(/\/accounts$/);
  await expect(page.getByRole("heading", { level: 1, name: "Accounts" })).toBeVisible();
  const rows = page.getByRole("grid", { name: "Accounts" }).locator("tbody tr");
  await expect(rows).toHaveCount(5);
  for (const name of ALL) await expect(page.getByRole("link", { name })).toBeVisible();
});

test("accounts table shows each primary contact and phone", async ({ page }) => {
  const row = page.getByRole("grid", { name: "Accounts" }).locator("tbody tr", { hasText: "Delta Fintech" });
  await expect(row.getByText("Sofia Lindqvist")).toBeVisible();
  await expect(row.getByText("+44 20 7946 0321")).toBeVisible();
});

const searches: [string, string[]][] = [
  ["evergreen", ["Evergreen Retail"]],
  ["EVERGREEN", ["Evergreen Retail"]],
  ["  Delta  ", ["Delta Fintech"]],
  ["C-1003", ["Cardinal Logistics"]],
  ["c-1003", ["Cardinal Logistics"]],
  ["1002", ["Blue Ridge Health"]],
  ["C-10", ALL],
  ["health", ["Blue Ridge Health"]],
];

for (const [query, expected] of searches) {
  test(`search "${query}" finds ${expected.length} account(s)`, async ({ page }) => {
    await page.getByRole("textbox", { name: "Search accounts" }).fill(query);
    const rows = page.getByRole("grid", { name: "Accounts" }).locator("tbody tr");
    await expect(rows).toHaveCount(expected.length);
    for (const name of expected) await expect(page.getByRole("link", { name })).toBeVisible();
  });
}

test("search with no matches shows the empty state", async ({ page }) => {
  await page.getByRole("textbox", { name: "Search accounts" }).fill("zzz-no-such-account");
  await expect(page.getByRole("heading", { name: "No accounts match" })).toBeVisible();
});

test("clearing the search restores the full list", async ({ page }) => {
  const box = page.getByRole("textbox", { name: "Search accounts" });
  await box.fill("delta");
  await expect(page.getByRole("grid", { name: "Accounts" }).locator("tbody tr")).toHaveCount(1);
  await page.getByRole("button", { name: "Reset" }).click();
  await expect(box).toHaveValue("");
  await expect(page.getByRole("grid", { name: "Accounts" }).locator("tbody tr")).toHaveCount(5);
});

test("clicking an account opens its 360 view", async ({ page }) => {
  await page.getByRole("link", { name: "Cardinal Logistics" }).click();
  await expect(page).toHaveURL(/\/accounts\/C-1003$/);
  await expect(page.getByRole("heading", { level: 1, name: "Cardinal Logistics" })).toBeVisible();
});

test("API failure shows an error instead of a blank page", async ({ page, consoleErrors }) => {
  await page.route("**/v1/customers?**", (r) => r.fulfill({ status: 500, json: { detail: "warehouse offline" } }));
  await page.getByRole("textbox", { name: "Search accounts" }).fill("acme");
  await expect(page.getByText("Could not load data")).toBeVisible();
  await expect(page.getByText("warehouse offline")).toBeVisible();
  // The browser logs the simulated 500s; those are expected here.
  consoleErrors.splice(0, consoleErrors.length, ...consoleErrors.filter((e) => !/status of 500/.test(e)));
});
