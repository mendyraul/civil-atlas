import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './acceptance',
  testMatch: 'licensing-live.spec.ts',
  workers: 1,
  use: { baseURL: 'http://127.0.0.1:3102', ...devices['Desktop Chrome'] },
  webServer: {
    command: 'npm run dev -- --port 3102',
    url: 'http://127.0.0.1:3102/atlas',
    reuseExistingServer: false,
    env: {
      NEXT_PUBLIC_DEMO_MODE: 'false',
      NEXT_PUBLIC_API_BASE_URL: 'https://public-api.fixture.invalid',
      NEXT_PUBLIC_MAP_STYLE_URL: '/map-styles/minimal.json',
    },
  },
  reporter: process.env.CI ? 'github' : 'list',
});
