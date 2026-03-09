import { test } from "@playwright/test";
import { login } from "./auth.setup";
import * as fs from "fs";
import * as path from "path";

const THEME = (process.env.DEMO_THEME || "dark") as "dark" | "light";
const DEMO_DIR = path.join(__dirname, "..", "docs", "demo");
const FRAME_DIR = path.join(DEMO_DIR, `frames-${THEME}`);
const CHROME_HTML = path.join(
  __dirname,
  THEME === "light" ? "browser-chrome-light.html" : "browser-chrome.html"
);
const OUTPUT_VIDEO = path.join(DEMO_DIR, `demo-${THEME}.mp4`);

// App viewport (16:9)
const APP_W = 1440;
const APP_H = 810;

// Final frame size (chrome wrapper adds padding + title bar)
const FRAME_W = APP_W + 140; // 70px padding each side
const FRAME_H = APP_H + 44 + 140; // 44px title bar + 140px padding

const FPS = 30;

const beat = (ms = 600) => new Promise((r) => setTimeout(r, ms));

/**
 * Render a screenshot inside macOS-style browser chrome and capture the result.
 */
async function wrapInChrome(
  chromePage: import("@playwright/test").Page,
  screenshotPath: string,
  frameIndex: number,
  holdFrames = 1
) {
  const html = fs.readFileSync(CHROME_HTML, "utf-8");
  const imgBase64 = fs.readFileSync(screenshotPath).toString("base64");
  const imgSrc = `data:image/png;base64,${imgBase64}`;

  await chromePage.setContent(html, { waitUntil: "load" });
  await chromePage
    .locator(".content img")
    .evaluate((el, src) => el.setAttribute("src", src), imgSrc);
  await chromePage.waitForTimeout(50);

  for (let i = 0; i < holdFrames; i++) {
    const idx = String(frameIndex + i).padStart(5, "0");
    await chromePage.screenshot({
      path: path.join(FRAME_DIR, `frame-${idx}.png`),
      fullPage: false,
    });
  }

  return frameIndex + holdFrames;
}

test("Demo walkthrough", async ({ browser }, testInfo) => {
  testInfo.setTimeout(600_000);

  // Clean/create frame output directory
  if (fs.existsSync(FRAME_DIR)) {
    fs.rmSync(FRAME_DIR, { recursive: true });
  }
  fs.mkdirSync(FRAME_DIR, { recursive: true });

  // Chrome wrapper page — 2x scale for retina-quality frames
  const chromeContext = await browser.newContext({
    viewport: { width: FRAME_W, height: FRAME_H },
    deviceScaleFactor: 2,
    colorScheme: THEME,
  });
  const chromePage = await chromeContext.newPage();

  // App page — 2x scale for sharp text rendering
  const appContext = await browser.newContext({
    viewport: { width: APP_W, height: APP_H },
    deviceScaleFactor: 2,
    colorScheme: THEME,
  });
  const page = await appContext.newPage();

  // Set theme before app loads
  await page.goto("/");
  await page.evaluate((t) => localStorage.setItem("theme", t), THEME);
  await page.goto("/");

  let frameIdx = 0;

  /** Capture a single frame, duplicated holdFrames times */
  async function snap(holdFrames = 1) {
    const tmpPath = path.join(FRAME_DIR, `_tmp.png`);
    await page.screenshot({ path: tmpPath, fullPage: false });
    frameIdx = await wrapInChrome(chromePage, tmpPath, frameIdx, holdFrames);
    fs.unlinkSync(tmpPath);
  }

  /** Hold on current view for a duration */
  async function hold(ms: number) {
    const frames = Math.max(1, Math.round((ms / 1000) * FPS));
    await snap(frames);
  }

  /**
   * Continuously capture frames for `durationMs`, taking a fresh screenshot
   * every `intervalMs` to show live UI changes (typing, streaming, etc).
   */
  async function captureLoop(durationMs: number, intervalMs = 80) {
    const end = Date.now() + durationMs;
    while (Date.now() < end) {
      await snap(1);
      await page.waitForTimeout(intervalMs);
    }
  }

  /** Find the chat scroll container */
  function getChatContainer() {
    return page.evaluate(() => {
      const scrollables = Array.from(document.querySelectorAll('[class*="overflow-y-auto"]'));
      const chat = scrollables.find((el) => el.scrollHeight > 500 && el.clientHeight > 300);
      return !!chat;
    });
  }

  /**
   * Smooth scroll with ease-in-out curve.
   * Scrolls the chat container if present, otherwise window.
   */
  async function smoothScroll(deltaY: number, durationMs = 800) {
    const steps = Math.round((durationMs / 1000) * FPS);
    let scrolled = 0;
    for (let i = 0; i < steps; i++) {
      // Ease-in-out: smooth acceleration and deceleration
      const t = (i + 1) / steps;
      const eased = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
      const target = deltaY * eased;
      const stepDelta = target - scrolled;
      scrolled = target;

      await page.evaluate((d) => {
        const scrollables = Array.from(document.querySelectorAll('[class*="overflow-y-auto"]'));
        const chat = scrollables.find((el) => el.scrollHeight > 500 && el.clientHeight > 300);
        if (chat) {
          chat.scrollTop += d;
        } else {
          window.scrollBy(0, d);
        }
      }, stepDelta);
      await snap(1);
      await page.waitForTimeout(Math.round(durationMs / steps));
    }
  }

  // --- Walkthrough ---

  await login(page);
  await beat(500);

  // Delete duplicate "Analyze my GME position" conversations
  await page.evaluate(async () => {
    const cookies = document.cookie;
    const csrfMatch = cookies.match(/csrftoken=([^;]+)/);
    const csrf = csrfMatch ? csrfMatch[1] : "";
    const res = await fetch("/api/chat/conversations/", { credentials: "include" });
    const convos = await res.json();
    const dupes = (convos.results || convos).filter(
      (c: { title: string }) => c.title === "Analyze my GME position"
    );
    for (const c of dupes) {
      await fetch(`/api/chat/conversations/${c.id}/`, {
        method: "DELETE",
        credentials: "include",
        headers: { "X-CSRFToken": csrf },
      });
    }
  });
  await page.goto("/");
  await beat(500);

  await hold(1200); // Home view — brief orient

  // Type a question
  const input = page.locator("textarea").first();
  await input.click();
  await beat(200);

  const msg = "Analyze my GME position";
  for (let i = 0; i < msg.length; i++) {
    await page.keyboard.type(msg[i], { delay: 20 });
    await snap(2); // 2 frames per character ≈ 15 chars/sec at 30fps
  }
  await hold(400); // Brief pause on completed text

  // Send the message
  await page.keyboard.press("Enter");

  // Smoothly follow the streaming content as it appears.
  // Gently ease scroll toward the bottom each frame — like a human
  // slowly scrolling down while reading incoming text.
  // Detect streaming end by checking if the textarea is re-enabled.
  {
    const maxCapture = Date.now() + 90_000;
    while (Date.now() < maxCapture) {
      // Gently ease scroll toward the bottom (lerp — never jumps)
      await page.evaluate(() => {
        const scrollables = Array.from(document.querySelectorAll('[class*="overflow-y-auto"]'));
        const chat = scrollables.find((el) => el.scrollHeight > 500 && el.clientHeight > 300);
        if (chat) {
          const target = chat.scrollHeight - chat.clientHeight;
          const distance = target - chat.scrollTop;
          if (distance > 1) {
            chat.scrollTop += distance * 0.08;
          }
        }
      });

      await snap(1);
      await page.waitForTimeout(80);

      // Textarea is disabled during streaming, enabled when done
      const done = await page
        .evaluate(() => {
          const ta = document.querySelector("textarea");
          return ta ? !ta.disabled : false;
        })
        .catch(() => false);
      if (done) break;
    }

    // Let the scroll finish settling to the bottom
    for (let i = 0; i < 30; i++) {
      await page.evaluate(() => {
        const scrollables = Array.from(document.querySelectorAll('[class*="overflow-y-auto"]'));
        const chat = scrollables.find((el) => el.scrollHeight > 500 && el.clientHeight > 300);
        if (chat) {
          const target = chat.scrollHeight - chat.clientHeight;
          const distance = target - chat.scrollTop;
          if (distance > 1) chat.scrollTop += distance * 0.15;
        }
      });
      await snap(1);
      await page.waitForTimeout(33);
    }

    // Hold on the finished response
    await hold(1500);
  }

  // --- Quick panel tour ---

  const sidebar = page.locator("aside");

  // Portfolio
  await sidebar.locator('button:has-text("Portfolio")').click();
  await page.waitForSelector('[role="dialog"]', { timeout: 10_000 });
  await beat(300);
  await captureLoop(300);
  await hold(1500);

  // Budgets
  const nav = page.locator('[role="dialog"] nav');
  await nav.locator('button:has-text("Budgets")').click();
  await beat(200);
  await captureLoop(200);
  await hold(1500);

  // Goals — end on this view
  await nav.locator('button:has-text("Goals")').click();
  await beat(200);
  await captureLoop(200);
  await hold(2000);

  // Clean up chrome context
  await appContext.close();
  await chromeContext.close();

  // Stitch frames into video with ffmpeg
  // -crf 12 for near-lossless, -preset slow for better compression
  const { execSync } = await import("child_process");
  try {
    execSync(
      `ffmpeg -y -framerate ${FPS} -i "${FRAME_DIR}/frame-%05d.png" ` +
        `-c:v libx264 -preset slow -crf 12 -pix_fmt yuv420p ` +
        `-vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" "${OUTPUT_VIDEO}"`,
      { stdio: "pipe" }
    );
    console.log(`Video saved to ${OUTPUT_VIDEO} (${frameIdx} frames at ${FPS}fps)`);
  } catch (e: unknown) {
    const errMsg = e instanceof Error ? e.message : String(e);
    console.warn(`ffmpeg failed (install ffmpeg to generate video): ${errMsg}`);
    console.log(`Frames saved to ${FRAME_DIR} (${frameIdx} frames)`);
  }
});
