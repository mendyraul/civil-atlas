import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: './e2e',
  // Software-rendered maps compete for CPU on the CI runner, especially when
  // another scenario opens two comparison canvases. Keep their execution serial.
  workers: process.env.CI ? 1 : undefined,
  use: { baseURL: 'http://127.0.0.1:3000', ...devices['Desktop Chrome'] },
  webServer: { command: 'npm run dev', url: 'http://127.0.0.1:3000/atlas', reuseExistingServer: !process.env.CI },
  reporter: process.env.CI ? 'github' : 'list',
});
