import { expect, test } from '@playwright/test';

test('unavailable basemap offers a recoverable failure state', async ({ page }) => {
  await page.route('**/map-styles/minimal.json', (route) => route.abort());
  await page.route('**/unavailable-style.json', (route) => route.abort());
  await page.goto('/atlas');
  const map = page.getByRole('group', { name: /Interactive historical atlas map/i });
  await expect(map.getByRole('alert')).toContainText(/unavailable/i);
  await expect(map.getByRole('button', { name: /retry map/i })).toBeEnabled();
});
