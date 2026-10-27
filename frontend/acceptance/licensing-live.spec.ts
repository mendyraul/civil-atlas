import { expect, test } from '@playwright/test';
import fixture from './fixtures/boundary-readings.json';

test('published border readings preserve source credits, visibility and shared choices', async ({ page }) => {
  // The backend contract test first keeps these records private, then approves
  // them through the editorial API and verifies this exact public wire shape.
  await page.route('https://public-api.fixture.invalid/api/v1/**', async (route) => {
    const path = new URL(route.request().url()).pathname;
    const json = path === '/api/v1/world/117' ? fixture.world : path === '/api/v1/sources' ? fixture.sources : [];
    await route.fulfill({ headers: { 'Access-Control-Allow-Origin': '*' }, json });
  });
  await page.goto('/atlas');
  await page.getByRole('button', { name: /Layers & research/ }).click();
  const primary = page.getByRole('checkbox', { name: /Synthetic primary reading/ });
  const alternative = page.getByRole('checkbox', { name: /Synthetic alternative reading/ });
  await expect(primary).toBeChecked();
  await expect(alternative).not.toBeChecked();
  await expect(page.getByText('Synthetic private reading', { exact: true })).toHaveCount(0);
  const credits = page.locator('.maplibregl-ctrl-attrib-inner');
  await expect(credits).not.toContainText('Cliopatria');

  await primary.uncheck();
  await alternative.check();
  await expect(credits).toContainText('Borders: Cliopatria (Seshat)');
  await expect(credits.getByRole('link', { name: 'CC BY 4.0' })).toHaveAttribute('href', 'https://creativecommons.org/licenses/by/4.0/');
  await expect(page.getByRole('region', { name: 'Boundary interpretations' }).locator('a[href="/sources/acceptance-source-alternative"]')).toBeVisible();
  await expect(page).toHaveURL(/boundaries=acceptance-reading-alternative/);
  await expect(page).toHaveURL(/hiddenBoundaries=acceptance-reading-primary/);

  await page.reload();
  await page.getByRole('button', { name: /Layers & research/ }).click();
  await expect(primary).not.toBeChecked();
  await expect(alternative).toBeChecked();
  await expect(credits).toContainText('Cliopatria');

  await page.getByRole('button', { name: /Civilization extents/ }).click();
  await expect(credits).not.toContainText('Cliopatria');
  await page.getByRole('button', { name: /Civilization extents/ }).click();
  await expect(credits).toContainText('Cliopatria');
  await alternative.uncheck();
  await expect(primary).not.toBeChecked();
  await expect(credits).not.toContainText('Cliopatria');
});
