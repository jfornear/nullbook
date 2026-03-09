import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  outputDir: "./e2e/results",
  timeout: 60_000,
  retries: 0,
  use: {
    baseURL: "http://127.0.0.1:5173",
    viewport: { width: 1440, height: 810 },
    deviceScaleFactor: 2,
    colorScheme: "dark",
    screenshot: "off",
  },
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
  webServer: undefined, // Assumes `make dev` is already running
});
