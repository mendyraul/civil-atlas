import { expect, test } from '@playwright/test';
test.skip(!process.env.NEXT_PUBLIC_MAP_STYLE_URL, 'Run with a deliberately unavailable style URL');
test('unavailable basemap is recoverable',async({page})=>{await page.route('**/unavailable-style.json',route=>route.abort()); await page.goto('/atlas'); const map=page.getByRole('group',{name:/Interactive historical atlas map/i}); await expect(map.getByRole('alert')).toContainText(/unavailable/i); await expect(map.getByRole('button',{name:/retry map/i})).toBeEnabled();});
