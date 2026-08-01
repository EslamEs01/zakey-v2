import { defineConfig } from "@playwright/test";

const BASE_URL = "http://127.0.0.1:8000";
const VIEWPORT_HEIGHT = 1200;
const VIEWPORT_WIDTHS = [1440, 1024, 768, 390];
const NO_JS_TEST = /no-js\.spec\.js/;

function chromeProject(width) {
  return {
    name: `chrome-${width}`,
    testIgnore: NO_JS_TEST,
    use: browserUse(width),
  };
}

function noJavaScriptProject(width) {
  return {
    name: `no-js-${width}`,
    testMatch: NO_JS_TEST,
    use: { ...browserUse(width), javaScriptEnabled: false },
  };
}

function browserUse(width) {
  return {
    baseURL: BASE_URL,
    channel: "chrome",
    colorScheme: "light",
    locale: "ar-EG",
    screenshot: "only-on-failure",
    timezoneId: "Africa/Cairo",
    trace: "retain-on-failure",
    viewport: { width, height: VIEWPORT_HEIGHT },
  };
}

export default defineConfig({
  testDir: "./tests",
  timeout: 180_000,
  outputDir: "./specs/003-zakey-frontend-reference-build/qa/playwright-results",
  fullyParallel: true,
  forbidOnly: true,
  retries: 0,
  workers: 4,
  reporter: [["line"]],
  expect: {
    timeout: 10_000,
  },
  use: {
    actionTimeout: 10_000,
    navigationTimeout: 30_000,
  },
  projects: [
    ...VIEWPORT_WIDTHS.map(chromeProject),
    ...VIEWPORT_WIDTHS.map(noJavaScriptProject),
  ],
  webServer: {
    command: "uv run python manage.py runserver 127.0.0.1:8000 --noreload",
    url: `${BASE_URL}/`,
    reuseExistingServer: false,
    timeout: 120_000,
    stdout: "pipe",
    stderr: "pipe",
  },
});
