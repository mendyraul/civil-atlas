import { describe, expect, it } from 'vitest';
import { sourceCatalog, world117 } from '../data/demoWorld117';
import { filterWorldByYear } from './atlas';
import { isCliopatria } from './research';
import { civilizationLabels } from './cartography';
import type { GeoJSONPosition, TerritorialGeometry } from '../types/atlas';

// Independent point-in-polygon checks catch the former broad demo envelopes.
function contains(geometry: TerritorialGeometry, [x, y]: GeoJSONPosition) {
  const inRing = (ring: GeoJSONPosition[]) => {
    let inside = false;
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const [ax, ay] = ring[i], [bx, by] = ring[j];
      if ((ay > y) !== (by > y) && x < (bx - ax) * (y - ay) / (by - ay) + ax) inside = !inside;
    }
    return inside;
  };
  const polygons = geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates;
  return polygons.some(([outer, ...holes]) => inRing(outer) && !holes.some(inRing));
}

describe('deployed preview boundaries', () => {
  it('ships only reviewed source geometry with resolvable citations', () => {
    expect(world117.layers.length).toBeGreaterThan(0);
    for (const layer of world117.layers) {
      expect(layer.reviewStatus).toBe('reviewed');
      expect(layer.isPlaceholder || Boolean(layer.geometryPlaceholder)).toBe(false);
      expect(isCliopatria(layer, sourceCatalog)).toBe(true);
      expect(layer.sourceRecordIds.every((id) => sourceCatalog.some((source) => source.id === id))).toBe(true);
    }
  });

  it('includes Roman land on both Mediterranean shores while preserving sea gaps', () => {
    const rome = world117.layers.find((layer) => layer.civilizationId === 'roman-empire')!;
    for (const point of [[12.5, 41.9], [9, 36], [-4, 39], [14, 37.5]] as GeoJSONPosition[]) {
      expect(contains(rome.geometryJson, point)).toBe(true);
    }
    for (const point of [[15, 34.5], [15, 38.7]] as GeoJSONPosition[]) {
      expect(contains(rome.geometryJson, point)).toBe(false);
    }
  });

  it('withdraws geometry outside its source interval without a schematic fallback', () => {
    const rome = world117.layers.find((layer) => layer.civilizationId === 'roman-empire')!;
    expect(filterWorldByYear(world117, rome.validToYear).layers).toContain(rome);
    expect(filterWorldByYear(world117, rome.validToYear + 1).layers.some((layer) => layer.civilizationId === rome.civilizationId)).toBe(false);
  });

  it('places a single label inside each polity instead of repeating on islands', () => {
    const labels = civilizationLabels(world117.layers, world117.civilizations).features;
    expect(new Set(labels.map((label) => label.id)).size).toBe(labels.length);
    for (const label of labels) {
      const layer = world117.layers.find((candidate) => candidate.civilizationId === label.id)!;
      expect(contains(layer.geometryJson, label.geometry.coordinates)).toBe(true);
    }
  });
});
