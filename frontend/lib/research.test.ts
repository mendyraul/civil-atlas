import { describe, expect, it } from 'vitest';
import { availableLayers, isCliopatria, visibleBoundaryLayers } from './research';
import { normalizeApiPayload } from './atlas';
import type { CivilizationLayer, SourceRecord } from '../types/atlas';
const layer = (id: string, primary = false): CivilizationLayer => ({ id, civilizationId: 'rome', name: id, layerType: 'source_reported_extent', interpretationKind: 'boundary_variant', variantGroup: 'roman-frontier', isPrimary: primary, displayOrder: 1, validFromYear: 117, validToYear: 117, geometryJson: { type: 'Polygon', coordinates: [[[0, 0], [1, 0], [1, 1], [0, 0]]] }, confidence: 'low', reviewStatus: 'reviewed', sourceNote: 'A source interpretation', sourceRecordIds: ['cliopatria-record'], claimIds: [] });
const sources = [{ id: 'cliopatria-record', sourceNamespace: 'cliopatria' }] as SourceRecord[];
describe('research layers', () => {
  it('resolves datasets through source IDs and excludes unreviewed Cliopatria layers', () => {
    const reviewed = layer('reviewed'); const pending = { ...layer('pending'), reviewStatus: 'needs_review' as const };
    expect(isCliopatria(reviewed, sources)).toBe(true);
    expect(availableLayers([reviewed, pending], sources)).toEqual([reviewed]);
    expect(isCliopatria({ ...reviewed, sourceRecordIds: ['other'], name: 'Cliopatria' }, sources)).toBe(false);
  });
  it('defaults to primary boundaries and allows explicit alternatives and empty selections', () => {
    const primary = layer('primary', true), alternative = layer('alternative');
    expect(visibleBoundaryLayers([primary, alternative], {})).toEqual([primary]);
    expect(visibleBoundaryLayers([primary, alternative], { primary: false, alternative: true })).toEqual([alternative]);
    expect(visibleBoundaryLayers([primary], { primary: false })).toEqual([]);
    expect(visibleBoundaryLayers([alternative], {})).toEqual([alternative]);
  });
  it('does not suppress independent thematic layers', () => {
    const thematic = { ...layer('influence'), interpretationKind: 'influence_zone' as const };
    expect(visibleBoundaryLayers([layer('primary', true), thematic], {})).toContain(thematic);
  });
  it('normalizes backend fields without rewriting enum values or geometry', () => {
    expect(normalizeApiPayload({ source_namespace: 'cliopatria', review_status: 'needs_review', geometry_json: { type: 'MultiPolygon', coordinates: [] } })).toEqual({ sourceNamespace: 'cliopatria', reviewStatus: 'needs_review', geometryJson: { type: 'MultiPolygon', coordinates: [] } });
  });
});

it('prefers reviewed source geometry over a schematic primary interpretation', () => {
  const placeholder = { ...layer('schematic', true), reviewStatus: 'seeded' as const, isPlaceholder: true };
  const sourced = layer('sourced');
  expect(visibleBoundaryLayers([placeholder, sourced], {})).toEqual([sourced]);
});
