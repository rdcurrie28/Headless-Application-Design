import { test, expect } from "./fixtures";

test.describe("Evergreen Retail (C-1005)", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/accounts/C-1005");
    await expect(page.getByRole("heading", { level: 1, name: "Evergreen Retail" })).toBeVisible();
  });

  test("header shows motion and account facts", async ({ page }) => {
    const hero = page.locator(".ci-hero");
    await expect(hero.getByText("Retain", { exact: true })).toBeVisible();
    for (const value of ["C-1005", "Commercial", "NA-West", "mpatel", "001A000005"]) {
      await expect(hero.getByText(value, { exact: true })).toBeVisible();
    }
  });

  test("header shows the primary contact with a callable phone number", async ({ page }) => {
    const contact = page.getByLabel("Primary contact");
    await expect(contact.getByText("Tom Okafor")).toBeVisible();
    await expect(contact.getByText("1220 NW Lovejoy St, Portland, OR 97209")).toBeVisible();
    await expect(contact.getByRole("link", { name: "+1 (503) 555-0164" })).toHaveAttribute("href", "tel:+15035550164");
  });

  test("summary strip shows the KPIs", async ({ page }) => {
    const strip = page.getByLabel("Account summary");
    const kpi = (label: string) => strip.locator(".ci-kpi", { hasText: label }).locator(".ci-kpi-value");
    await expect(kpi("Active ARR")).toHaveText("$33K");
    await expect(kpi("Active SKUs")).toHaveText("1");
    await expect(kpi("Avg product health")).toHaveText("18");
    await expect(kpi("At-risk SKUs")).toHaveText("1");
    await expect(kpi("Churn propensity")).toHaveText("86");
    await expect(kpi("Expansion propensity")).toHaveText("5");
  });

  test("section cards render their data", async ({ page }) => {
    const skus = page.getByRole("grid", { name: "SKUs by customer" });
    await expect(skus.getByText("RHEL Server Premium")).toBeVisible();
    await expect(skus.getByText("$33,000")).toBeVisible();

    const health = page.getByRole("grid", { name: "Product health" });
    await expect(health.getByText("At risk")).toBeVisible();
    await expect(health.getByText("-41%")).toBeVisible();

    const propensity = page.locator(".pf-v6-c-card", { has: page.getByRole("heading", { name: "Propensity" }) });
    await expect(propensity.getByRole("progressbar", { name: "Churn propensity" })).toHaveAttribute("aria-valuenow", "86");
    await expect(propensity.getByText("Champion left")).toBeVisible();

    const doc = page.getByRole("link", { name: "qbr-2026-q3.pdf" });
    await expect(doc).toHaveAttribute("target", "_blank");
    await expect(doc).toHaveAttribute("rel", /noreferrer/);
  });

  test("breadcrumb returns to accounts", async ({ page }) => {
    await page.locator(".ci-crumbs").getByRole("link", { name: "Accounts" }).click();
    await expect(page).toHaveURL(/\/accounts$/);
  });

  test("refresh button refetches without errors", async ({ page }) => {
    const refetch = page.waitForResponse((r) => r.url().endsWith("/v1/customers/C-1005/360") && r.ok());
    await page.getByRole("button", { name: "Refresh" }).click();
    await refetch;
    await expect(page.getByRole("heading", { level: 1, name: "Evergreen Retail" })).toBeVisible();
  });
});

test("logging a next step adds it to the account", async ({ page }) => {
  const note = `QA follow-up ${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
  await page.goto("/accounts/C-1002");
  await page.getByRole("button", { name: "Add" }).click();

  const modal = page.getByRole("dialog", { name: "Log a next step" });
  const save = modal.getByRole("button", { name: "Save" });
  await expect(save).toBeDisabled();

  await modal.getByLabel("Type").selectOption("renewal");
  await modal.getByLabel("Note").fill(note);
  await expect(save).toBeDisabled();
  await modal.getByLabel("Logged by").fill("qa-bot");
  await modal.getByLabel("Due date").fill("2026-12-01");
  await expect(save).toBeEnabled();
  await save.click();

  await expect(modal).toBeHidden();
  await expect(page.getByText(note)).toBeVisible();
});

test("cancelling the next-step modal saves nothing", async ({ page }) => {
  await page.goto("/accounts/C-1004");
  await page.getByRole("button", { name: "Add" }).click();
  const modal = page.getByRole("dialog", { name: "Log a next step" });
  await modal.getByLabel("Note").fill("should not be saved");
  await modal.getByRole("button", { name: "Cancel" }).click();
  await expect(modal).toBeHidden();
  await expect(page.getByText("should not be saved")).toHaveCount(0);
});

test("a failed section shows a warning but the rest of the page loads", async ({ page }) => {
  await page.route("**/v1/customers/C-1005/360", async (route) => {
    const res = await route.fetch();
    const body = await res.json();
    body.skus = null;
    body.errors = [{ section: "skus", source: "snowflake", message: "timeout" }];
    await route.fulfill({ response: res, json: body });
  });
  await page.goto("/accounts/C-1005");
  await expect(page.getByText("Some sections couldn't load")).toBeVisible();
  await expect(page.getByText("This section is temporarily unavailable")).toHaveCount(1);
  await expect(page.getByRole("grid", { name: "Product health" })).toBeVisible();
});

test("unknown account shows an error", async ({ page, consoleErrors }) => {
  await page.goto("/accounts/C-9999");
  await expect(page.getByText("Could not load this account")).toBeVisible();
  // The browser logs the expected 404 for the API call; that one is fine.
  consoleErrors.splice(0, consoleErrors.length, ...consoleErrors.filter((e) => !/404/.test(e)));
});
