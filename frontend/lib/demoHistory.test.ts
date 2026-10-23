import { describe, expect, it } from 'vitest';
import { loadDemoWorld, previewSources } from './demoHistory';
import { historicalCatalog } from '../data/history/catalog';

describe('expanded historical preview', () => {
  it.each([
    [-500, ['achaemenid-empire', 'roman-republic']],
    [117, ['roman-empire', 'han-dynasty', 'kushan-empire']],
    [700, ['tang-dynasty', 'umayyad-caliphate']],
    [1230, ['mongol-empire']],
    [1500, ['ottoman-empire', 'ming-dynasty', 'aztec-triple-alliance']],
    [1750, ['qing-dynasty', 'russian-empire', 'spanish-empire']],
  ] as const)('loads original dated geometry at %i', async (year, expected) => {
    const world = await loadDemoWorld(year);
    expect(world.year).toBe(year);
    expect(world.civilizations.map((civilization) => civilization.id)).toEqual(expect.arrayContaining([...expected]));
    for (const layer of world.layers) {
      expect(layer.validFromYear).toBeLessThanOrEqual(year);
      expect(layer.validToYear).toBeGreaterThanOrEqual(year);
      expect(layer.isPlaceholder).toBe(false);
      expect(layer.sourceRecordIds.every((id) => previewSources.some((source) => source.id === id))).toBe(true);
    }
  });

  it('changes source geometry at an inclusive interval boundary without carrying it forward', async () => {
    const row = historicalCatalog.rows.find((record) => record.civilizationId === 'mongol-empire' && record.validFromYear === 1206)!;
    expect((await loadDemoWorld(row.validToYear)).layers.some((layer) => layer.id === row.id)).toBe(true);
    const next = await loadDemoWorld(row.validToYear + 1);
    expect(next.layers.some((layer) => layer.id === row.id)).toBe(false);
    expect(next.layers.some((layer) => layer.civilizationId === 'mongol-empire')).toBe(true);
  });

  it('does not confuse unrelated polities with reused upstream Wikidata IDs', async () => {
    const world = await loadDemoWorld(1100);
    expect(world.layers.some((layer) => layer.civilizationId === 'han-dynasty')).toBe(false);
    expect(world.civilizations.some((civilization) => civilization.displayName === 'Chauhan Dynasty')).toBe(false);
  });

  it('rejects unsupported dates instead of substituting another year', async () => {
    await expect(loadDemoWorld(-601)).rejects.toThrow('coverage');
    await expect(loadDemoWorld(1801)).rejects.toThrow('coverage');
  });
});
