import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('globe has expandable research controls and keeps attribution visible', async ({ page }) => {
  await page.goto('/atlas');
  await expect(page.getByRole('application', { name: /historical atlas map/i })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'World at 117 CE' })).toBeVisible();
  await expect(page.getByRole('region', { name: 'Layers and research' })).toHaveCount(0);
  await page.getByRole('button', { name: /Layers & research/ }).click();
  await expect(page.getByRole('region', { name: 'Layers and research' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'OpenStreetMap' }).first()).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('button', { name: /Layers & research/ })).toBeFocused();
  await expect(page.getByRole('link', { name: /Source code/ })).toBeVisible();
});

test('selection survives refresh and selection opens the evidence drawer', async ({ page }) => {
  await page.goto('/atlas?y=117&sel=roman-empire');
  await page.reload();
  await page.getByRole('button', { name: /Layers & research/ }).click();
  await page.getByRole('button', { name: /Han Dynasty dynasty/i }).click();
  await expect(page).toHaveURL(/sel=han-dynasty/);
  await expect(page.getByRole('region', { name: 'Selection and evidence' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Han Dynasty', exact: true })).toBeVisible();
});

test('keyboard interaction changes timeline', async ({ page }) => {
  await page.goto('/atlas');
  await page.getByRole('slider', { name: 'Year' }).press('ArrowRight');
  await expect(page).toHaveURL(/y=118/);
});

test('later dates load sourced polities and modern context persists independently', async ({ page }) => {
  await page.goto('/atlas');
  await page.getByRole('button', { name: '1500 CE', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'World at 1500 CE' })).toBeVisible();
  await page.getByRole('button', { name: /Layers & research/ }).click();
  await expect(page.getByRole('button', { name: /Ming Dynasty dynasty/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /Ottoman Empire empire/ })).toBeVisible();
  await page.getByRole('button', { name: /^Present-day borders/ }).click();
  await expect(page).toHaveURL(/modernBorders=false/);
  await page.reload();
  await page.getByRole('button', { name: /Layers & research/ }).click();
  await expect(page.getByRole('button', { name: /^Present-day borders/ })).toHaveAttribute('aria-pressed', 'false');
  await expect(page.getByRole('button', { name: /Ming Dynasty dynasty/ })).toBeVisible();
});

test('explicit camera orientation survives initialization and refresh', async ({ page }) => {
  await page.goto('/atlas?y=117&sel=roman-empire&lng=100&lat=35&z=3&bearing=25&pitch=30');
  await expect(page.locator('.maplibregl-canvas')).toBeVisible();
  await expect(page.getByText('Loading basemap, labels, and atlas layers…')).toHaveCount(0);
  await page.waitForTimeout(1300);
  for (const [key, expected] of [['lng', 100], ['lat', 35], ['z', 3], ['bearing', 25], ['pitch', 30]] as const) {
    expect(Number(new URL(page.url()).searchParams.get(key))).toBeCloseTo(expected, 1);
  }
  await page.reload();
  await expect(page.getByText('Loading basemap, labels, and atlas layers…')).toHaveCount(0);
  await expect(page).toHaveURL(/pitch=30/);
});

test('mobile drawer is usable without horizontal page overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/atlas');
  await page.getByRole('button', { name: /Layers & research/ }).click();
  await expect(page.getByRole('region', { name: 'Layers and research' })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await page.getByRole('button', { name: /Close research panel/ }).click();
  await expect(page.getByRole('region', { name: 'Layers and research' })).toHaveCount(0);
});

test('source page explains license split and upstream credits', async ({ page }) => {
  await page.goto('/sources');
  await expect(page.getByRole('heading', { name: 'Data sources & licenses' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Borders · Cliopatria' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Full attribution register' })).toBeVisible();
});

test('later polities have working dossiers and searchable source citations', async ({ page }) => {
  await page.goto('/civilizations/ottoman-empire');
  await expect(page.getByRole('heading', { name: 'Ottoman Empire', exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: 'View this entity on the atlas' })).toHaveAttribute('href', /y=1305/);
  await page.goto('/sources?q=Ottoman');
  await expect(page.getByRole('link', { name: 'Cliopatria: Ottoman Empire' }).first()).toBeVisible();
  await page.getByRole('link', { name: 'Cliopatria: Ottoman Empire' }).first().click();
  await expect(page.getByRole('link', { name: /Open Ottoman Empire on atlas/ })).toHaveAttribute('href', /sel=ottoman-empire/);
});

test('@a11y atlas and open research panel have no automatically detectable violations', async ({ page }) => {
  await page.goto('/atlas');
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.getByRole('button', { name: /Layers & research/ }).click();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});

test('reduced motion disables autoplay', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/atlas');
  await expect(page.getByRole('button', { name: /Play/ })).toBeDisabled();
});
