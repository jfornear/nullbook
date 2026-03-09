import { test } from "@playwright/test";
import { login } from "./auth.setup";

const THEME = (process.env.DEMO_THEME || "dark") as "dark" | "light";
const SCREENSHOT_DIR = THEME === "light" ? "docs/screenshots-light" : "docs/screenshots";

async function snap(page: import("@playwright/test").Page, name: string) {
  await page.waitForTimeout(800);
  await page.screenshot({
    path: `${SCREENSHOT_DIR}/${name}.png`,
    fullPage: false,
  });
}

// Open a panel by clicking the sidebar button, then wait for the modal
async function openPanelFromSidebar(page: import("@playwright/test").Page, label: string) {
  const sidebarButton = page.locator("aside").locator(`button:has-text("${label}")`);
  await sidebarButton.click();
  await page.waitForSelector('[role="dialog"]', { timeout: 10_000 });
  await page.waitForTimeout(1000);
}

// Close the current modal
async function closeModal(page: import("@playwright/test").Page) {
  await page.keyboard.press("Escape");
  await page.waitForTimeout(500);
}

// Switch section inside the modal's left nav
async function switchModalSection(page: import("@playwright/test").Page, label: string) {
  const navButton = page.locator('[role="dialog"] nav').locator(`button:has-text("${label}")`);
  await navButton.click();
  await page.waitForTimeout(800);
}

test("Capture all screenshots", async ({ page }, testInfo) => {
  testInfo.setTimeout(120_000);

  // Set theme before app loads
  await page.goto("/");
  await page.evaluate((t) => localStorage.setItem("theme", t), THEME);

  // 01 - Login page (before auth)
  await page.goto("/");
  await page.waitForTimeout(500);
  const hasLogin = await page
    .locator("#username")
    .isVisible()
    .catch(() => false);
  if (!hasLogin) {
    await page.evaluate(async () => {
      const cookies = document.cookie;
      const csrfMatch = cookies.match(/csrftoken=([^;]+)/);
      if (csrfMatch) {
        await fetch("/api/auth/logout/", {
          method: "POST",
          credentials: "include",
          headers: { "X-CSRFToken": csrfMatch[1] },
        });
      }
    });
    await page.goto("/");
    await page.waitForTimeout(1000);
  }
  await page.waitForSelector("#username", { timeout: 5_000 });
  await snap(page, "01-login");

  // Log in once — reuse for all remaining screenshots
  await login(page);

  // 02 - Home view
  await snap(page, "02-home");

  // 03 - Accounts panel
  await openPanelFromSidebar(page, "Accounts");
  await snap(page, "03-accounts");

  // 05 - Transactions (navigate within the same modal)
  await switchModalSection(page, "Transactions");
  await snap(page, "05-transactions");

  // 07 - Budgets
  await switchModalSection(page, "Budgets");
  await snap(page, "07-budgets");

  // 08 - Goals
  await switchModalSection(page, "Goals");
  await snap(page, "08-goals");

  // 09 - Subscriptions
  await switchModalSection(page, "Subscriptions");
  await snap(page, "09-subscriptions");

  await closeModal(page);

  // 04 - Portfolio panel
  await openPanelFromSidebar(page, "Portfolio");
  await snap(page, "04-portfolio");
  await closeModal(page);

  // 06 - Taxes panel
  await openPanelFromSidebar(page, "Taxes");
  await snap(page, "06-taxes");
  await closeModal(page);

  // 10 - Import panel
  await openPanelFromSidebar(page, "Import");
  await snap(page, "10-import");
  await closeModal(page);

  // 11 - Settings
  const userButton = page.locator("aside").locator("text=jesse").first();
  await userButton.click();
  await page.waitForTimeout(500);
  await page.locator("text=Settings").click();
  await page.waitForSelector('[role="dialog"]', { timeout: 10_000 });
  await page.waitForTimeout(800);
  await snap(page, "11-settings-general");
});
