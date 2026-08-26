import { expect, test } from '@playwright/test';
test.skip(!process.env.NEXT_PUBLIC_MAP_STYLE_URL, 'Run with a deliberately unavailable style URL');
test('unavailable basemap is recoverable',async({page})=>{await page.route('**/unavailable-style.json',route=>route.abort()); await page.goto('/atlas'); await expect(page.getByRole('alert')).toContainText(/unavailable/i); await expect(page.getByRole('button',{name:/retry map/i})).toBeEnabled();});
