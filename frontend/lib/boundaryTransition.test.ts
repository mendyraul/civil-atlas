import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { BOUNDARY_FADE_MS, createBoundaryTransition, type BoundaryData } from './boundaryTransition';

let callbacks: Map<number, FrameRequestCallback>;
let sequence: number;
beforeEach(() => {
  callbacks = new Map(); sequence = 0;
  vi.stubGlobal('requestAnimationFrame', (callback: FrameRequestCallback) => { callbacks.set(++sequence, callback); return sequence; });
  vi.stubGlobal('cancelAnimationFrame', (id: number) => callbacks.delete(id));
});
afterEach(() => vi.unstubAllGlobals());
function frame(now: number) { const pending = [...callbacks.values()]; callbacks.clear(); pending.forEach((callback) => callback(now)); }
const snapshot = (id: string): BoundaryData => ({ type: 'FeatureCollection', features: [{ type: 'Feature', id, properties: { id }, geometry: { type: 'Polygon', coordinates: [[[0, 0], [1, 0], [1, 1], [0, 0]]] } }] });
function setup() {
  const write = vi.fn(), paint = vi.fn(), ready = vi.fn(() => true);
  const transition = createBoundaryTransition({ write, paint, ready });
  return { ...transition, write, paint, ready };
}

it('retains both exact geometries until source readiness and cross-fades without an empty frame', () => {
  const t = setup(), old = snapshot('old'), next = snapshot('new');
  t.update(old, true); t.update(next, true);
  const union = t.write.mock.lastCall![0] as BoundaryData;
  expect(union.features.map((feature) => feature.geometry)).toEqual([old.features[0].geometry, next.features[0].geometry]);
  expect(t.paint).toHaveBeenLastCalledWith(0, 1); // Only this generation fades; old tiles stay settled.
  t.ready.mockReturnValue(false); t.sourceReady(); expect(callbacks.size).toBe(0);
  t.ready.mockReturnValue(true); t.sourceReady();
  frame(0); frame(BOUNDARY_FADE_MS / 2);
  expect(t.paint).toHaveBeenLastCalledWith(0.5, 1);
  frame(BOUNDARY_FADE_MS);
  expect(t.write).toHaveBeenLastCalledWith(next);
  expect(t.write.mock.calls.every(([data]) => data.features.length > 0)).toBe(true);
});

it('coalesces rapid scrubs to the latest date without flashing an older outgoing snapshot', () => {
  const t = setup(), first = snapshot('first'), second = snapshot('second'), skipped = snapshot('skip'), latest = snapshot('latest');
  t.update(first, true); t.update(second, true); t.sourceReady(); frame(0);
  t.update(skipped, true); t.update(latest, true); frame(BOUNDARY_FADE_MS);
  expect(t.paint).toHaveBeenLastCalledWith(0, 2);
  const union = t.write.mock.lastCall![0] as BoundaryData;
  expect(union.features.map((feature) => feature.id)).toEqual(['outgoing:second', 'latest']);
  expect(union.features.every((feature) => feature.properties?.timelineGeneration === 2)).toBe(true);
  t.sourceReady(); frame(500); frame(500 + BOUNDARY_FADE_MS);
  expect(t.write).toHaveBeenLastCalledWith(latest);
});

it('clears empty selections immediately and cancels animations for reduced motion and disposal', () => {
  const t = setup(); t.update(snapshot('first'), true); t.update(snapshot('next'), true); t.sourceReady();
  const empty: BoundaryData = { type: 'FeatureCollection', features: [] };
  t.update(empty, true); expect(callbacks.size).toBe(0); expect(t.write).toHaveBeenLastCalledWith(empty);
  t.update(snapshot('another'), false); expect(callbacks.size).toBe(0);
  t.update(snapshot('fade'), true); t.sourceReady(); t.dispose();
  expect(callbacks.size).toBe(0);
});

it('leaves unchanged geometry fully opaque instead of fading it twice', () => {
  const t = setup(), old = snapshot('same');
  t.update(old, true); t.update({ ...old, features: [...old.features, ...snapshot('new').features] }, true);
  const union = t.write.mock.lastCall![0] as BoundaryData;
  expect(union.features.filter((feature) => feature.id === 'same')).toHaveLength(1);
  expect(union.features[0].properties?.timelineRole).toBeUndefined();
});
