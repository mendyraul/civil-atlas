import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('personal notes survive reload and can be edited and deleted', async ({ page }) => {
  await page.goto('/atlas');
  await page.getByRole('button', { name: 'Map notes', exact: true }).click();
  await page.getByRole('button', { name: 'Mark a place' }).click();
  await page.getByRole('button', { name: 'Map notes', exact: true }).click();
  const notes = page.getByRole('region', { name: 'Personal annotations' });
  await notes.getByLabel('Title', { exact: true }).fill('My Rome note');
  await notes.getByLabel('Note', { exact: true }).fill('A personal research question.');
  await notes.getByLabel('Longitude', { exact: true }).fill('12.5');
  await notes.getByLabel('Latitude', { exact: true }).fill('41.9');
  await notes.getByRole('button', { name: 'Add coordinate' }).click();
  await notes.getByRole('button', { name: 'Save personal note' }).click();
  await expect(notes.getByRole('button', { name: 'Edit My Rome note' })).toBeVisible();
  await page.reload();
  await page.getByRole('button', { name: 'Map notes', exact: true }).click();
  await expect(notes.getByRole('button', { name: 'Edit My Rome note' })).toBeVisible();
  await notes.getByRole('button', { name: 'Edit My Rome note' }).click();
  await notes.getByLabel('Title', { exact: true }).fill('Rome question');
  await notes.getByRole('button', { name: 'Save personal note' }).click();
  await notes.getByRole('button', { name: 'Delete Rome question' }).click();
  await expect(notes.getByRole('button', { name: 'Delete Rome question' })).toHaveCount(0);
});

test('linked maps synchronize actual cameras and preserve independent dates', async ({ page }) => {
  await page.goto('/compare?leftYear=117&rightYear=123');
  const left = page.getByRole('region', { name: 'Left comparison map', exact: true });
  const right = page.getByRole('region', { name: 'Right comparison map', exact: true });
  await expect(left.locator('.maplibregl-canvas')).toBeVisible();
  await expect(right.locator('.maplibregl-canvas')).toBeVisible();
  await expect(left.getByText('Loading basemap, labels, and atlas layers…')).toHaveCount(0);
  await expect(right.getByText('Loading basemap, labels, and atlas layers…')).toHaveCount(0);
  await left.getByRole('button', { name: 'Zoom in', exact: true }).click();
  await expect(left.getByLabel('Left camera')).toContainText('zoom 2.80');
  // Issue another command before the follower's longer animation settles.
  await left.getByRole('button', { name: 'Zoom in', exact: true }).click();
  await expect(left.getByLabel('Left camera')).toContainText('zoom 3.80');
  await expect(right.getByLabel('Right camera')).toContainText('zoom 3.80');
  await right.getByLabel('Right year', { exact: true }).fill('130');
  await expect(page).toHaveURL(/rightYear=130/);
  await expect(left.getByLabel('Left year', { exact: true })).toHaveValue('117');
  await page.reload();
  await expect(right.getByLabel('Right year', { exact: true })).toHaveValue('130');
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
});

test('episode step changes year and is resumable after reload', async ({ page }) => {
  await page.goto('/atlas');
  await page.getByRole('button', { name: 'Episodes', exact: true }).click();
  const episodes = page.getByRole('region', { name: 'Historical episodes', exact: true });
  await episodes.getByRole('button', { name: /connected.world/i }).first().click();
  await expect(episodes.getByText(/Step 1\/3/)).toBeVisible();
  await episodes.getByRole('button', { name: 'Next step', exact: true }).click();
  await expect(page).toHaveURL(/y=123/);
  await expect(page).toHaveURL(/episodeStep=/);
  await page.reload();
  const trigger = page.getByRole('button', { name: 'Episodes', exact: true });
  await expect(trigger).toHaveAttribute('aria-expanded', 'true');
  await expect(episodes.getByText(/Step 2\/3/)).toBeVisible();
  await episodes.getByRole('button', { name: 'Stop episode', exact: true }).click();
  await expect(page).not.toHaveURL(/episode=/);
});

test('geographic research sends explicit dates and radius and displays provenance', async ({ page }) => {
  let captured: Record<string, unknown> | undefined;
  await page.route('**/api/v1/research/query', async (route) => {
    if (route.request().method() === 'OPTIONS') return route.fulfill({ status: 204, headers: { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'content-type', 'Access-Control-Allow-Methods': 'POST' } });
    captured = route.request().postDataJSON();
    await route.fulfill({ headers: { 'Access-Control-Allow-Origin': '*' }, json: { summary: '1 matching record in Civil Atlas for 117.', items: [{ kind: 'nodes', record: { id: 'roma', label: 'Roma', confidence: 'low', review_status: 'reviewed' }, sources: [{ id: 'rome-source', citation: 'Synthetic citation for UI testing' }], url: '/atlas?y=117&sel=roma' }], total: 1, page: 1, page_size: 20, data_version: 'test-version', limitations: ['Coverage is incomplete.'], unlocated_count: 2 } });
  });
  await page.goto('/atlas?y=117');
  await page.getByRole('button', { name: 'Area query', exact: true }).click();
  const panel = page.getByRole('region', { name: 'Geographic research', exact: true });
  await panel.getByLabel('Area', { exact: true }).selectOption('radius');
  await panel.getByLabel('Longitude', { exact: true }).fill('12.5');
  await panel.getByLabel('Latitude', { exact: true }).fill('41.9');
  await panel.getByLabel('Radius (km)', { exact: true }).fill('50');
  await panel.getByRole('button', { name: 'Search 117 CE' }).click();
  await expect(panel.getByRole('link', { name: 'Roma', exact: true })).toBeVisible();
  expect(captured).toMatchObject({ year: 117, area: { center: [12.5, 41.9], radiusKm: 50 } });
  await expect(panel.getByText('Coverage is incomplete.')).toBeVisible();
  await expect(panel.getByRole('link', { name: 'Synthetic citation for UI testing' })).toBeVisible();
});

test('@a11y toolkit controls remain accessible', async ({ page }) => {
  await page.goto('/atlas');
  for (const name of ['Map notes', 'Area query', 'Episodes', 'Layer status']) {
    await page.getByRole('button', { name, exact: true }).click();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  }
});
