import AxeBuilder from "@axe-core/playwright";
import { test, expect, isMobile } from "./fixtures";

const PAGES = [
  { path: "/accounts", heading: "Accounts" },
  { path: "/watchlists/at-risk", heading: "At-risk watchlist" },
  { path: "/watchlists/expansion", heading: "Expansion targets" },
  { path: "/accounts/C-1005", heading: "Evergreen Retail" },
];

test("sidebar navigation reaches every screen and marks the current one", async ({ page }, info) => {
  await page.goto("/accounts");
  const nav = page.getByRole("navigation", { name: "Main" });
  const toggle = page.getByRole("button", { name: "Toggle navigation" });

  for (const [label, url] of [
    ["At-risk watchlist", /\/watchlists\/at-risk$/],
    ["Expansion targets", /\/watchlists\/expansion$/],
    ["Accounts", /\/accounts$/],
  ] as const) {
    if (isMobile(info.project.name)) {
      await expect(toggle).toHaveAttribute("aria-expanded", "false");
      await toggle.click();
    }
    await nav.getByRole("link", { name: label }).click();
    await expect(page).toHaveURL(url);
    if (isMobile(info.project.name)) await expect(toggle).toHaveAttribute("aria-expanded", "false");
    // On mobile the sidebar is closed (aria-hidden) after navigating, so query the DOM directly.
    await expect(page.locator("#page-sidebar a", { hasText: label })).toHaveAttribute("aria-current", "page");
  }
});

test("brand link goes home", async ({ page }) => {
  await page.goto("/watchlists/at-risk");
  await page.getByRole("link", { name: /Customer Insights/ }).click();
  await expect(page).toHaveURL(/\/accounts$/);
});

test("unknown route shows the not-found page", async ({ page }) => {
  await page.goto("/does-not-exist");
  await expect(page.getByRole("heading", { name: "Page not found" })).toBeVisible();
  await page.getByRole("link", { name: "Back to accounts" }).click();
  await expect(page).toHaveURL(/\/accounts$/);
});

test("theme: black masthead with red accent, red primary actions", async ({ page }) => {
  await page.goto("/accounts/C-1005");
  const masthead = page.locator(".pf-v6-c-masthead");
  await expect(masthead).toHaveCSS("background-color", "rgb(11, 11, 12)");
  await expect(masthead).toHaveCSS("border-bottom-color", "rgb(224, 0, 0)");
  await expect(page.locator(".ci-hero")).toHaveCSS("background-color", "rgb(11, 11, 12)");
  await expect(page.locator(".ci-kpi--feature")).toHaveCSS("background-color", "rgb(224, 0, 0)");
});

test("no horizontal scroll on any screen", async ({ page }) => {
  for (const p of PAGES) {
    await page.goto(p.path);
    await expect(page.getByRole("heading", { level: 1, name: p.heading })).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow, `horizontal overflow on ${p.path}`).toBeLessThanOrEqual(0);
  }
});

for (const p of PAGES) {
  test(`accessibility: no serious or critical axe violations on ${p.path}`, async ({ page }) => {
    await page.goto(p.path);
    await expect(page.getByRole("heading", { level: 1, name: p.heading })).toBeVisible();
    const { violations } = await new AxeBuilder({ page }).analyze();
    const bad = violations
      .filter((v) => v.impact === "serious" || v.impact === "critical")
      .map((v) => `${v.id} (${v.impact}): ${v.help} — ${v.nodes.length} node(s): ${v.nodes.slice(0, 3).map((n) => n.target.join(" ")).join(" | ")}`);
    expect(bad, "axe violations").toEqual([]);
  });
}

test("visual tour screenshots", async ({ page }, info) => {
  for (const p of PAGES) {
    await page.goto(p.path);
    await expect(page.getByRole("heading", { level: 1, name: p.heading })).toBeVisible();
    await page.evaluate(() => document.fonts.ready);
    const name = `${info.project.name}${p.path.replace(/\//g, "_")}.png`;
    await page.screenshot({ path: `e2e-screens/${name}`, fullPage: true });
  }
});
