import { type Page } from "@playwright/test";

export async function login(page: Page) {
  await page.goto("/");
  // Give the page time to render and check auth
  await page.waitForTimeout(2000);

  const hasLoginForm = await page
    .locator("#username")
    .isVisible()
    .catch(() => false);

  if (hasLoginForm) {
    await page.fill("#username", "jesse");
    await page.fill("#password", "demo");
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);
  }

  // Wait for sidebar — confirms authenticated and app is loaded
  await page.waitForSelector("aside", { timeout: 30_000 });
  await page.waitForTimeout(500);
}
