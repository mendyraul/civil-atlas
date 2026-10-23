import { readFileSync } from 'node:fs';
import { webcrypto } from 'node:crypto';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { parseNotes } from './annotations';
import { loadAsset, parseEpisode, validateEpisode } from './episodes';
import { connectedWorldDemo } from '../data/episodes';
import type { EpisodeAsset } from '../types/atlas';

afterEach(() => vi.unstubAllGlobals());
describe('personal and curated content boundaries', () => {
  it('round-trips the operator-authored episode contract without invented territory', () => {
    const text = readFileSync('../backend/data/imports/episodes/v1/connected-world-117.json', 'utf8');
    const { pack } = parseEpisode(text);
    expect(pack.steps.map((s) => s.year)).toEqual([117, 123, 130]);
    expect(pack.annotations.every((a) => a.kind === 'territory' && a.boundaryLayerId && !a.geometry)).toBe(true);
    expect(pack.reviewStatus).toBe('needs_review');
  });
  it('import preview makes no requests and rejects undeclared assets and path traversal', () => {
    const fetch = vi.fn(); vi.stubGlobal('fetch', fetch);
    expect(parseEpisode(JSON.stringify(connectedWorldDemo)).pack.id).toBe('connected-world-117');
    expect(fetch).not.toHaveBeenCalled();
    expect(() => parseEpisode(JSON.stringify({ schemaVersion: 1, pack: connectedWorldDemo, files: { '/private': {} } }))).toThrow(/undeclared/);
    const pack = structuredClone(connectedWorldDemo);
    pack.assets = [{ id: 'a', kind: 'image', path: 'maps/../../private.png', sha256: 'a'.repeat(64), byteLength: 1, attribution: 'test', license: 'CC-BY-4.0', bounds: [0, 0, 1, 1] }];
    expect(() => validateEpisode(pack)).toThrow(/path/);
  });
  it('cannot import freehand territory as a curated boundary', () => {
    const pack = structuredClone(connectedWorldDemo);
    pack.annotations = [{ id: 'a', title: 'fake border', note: '', validFromYear: 117, validToYear: 117, kind: 'territory', geometry: { type: 'Point', coordinates: [0, 0] }, sourceRecordIds: [], reviewStatus: 'reviewed', confidence: 'high' }];
    expect(() => validateEpisode(pack)).toThrow(/Territory/);
  });
  it('forces imported personal notes to remain unreviewed and rejects broken polygon rings', () => {
    const note = { id: 'a', title: 'Personal', note: 'Research note', validFromYear: 117, validToYear: 130, kind: 'explanation', geometry: { type: 'Point', coordinates: [12, 42] }, sourceRecordIds: [], reviewStatus: 'reviewed', confidence: 'low' };
    expect(parseNotes(JSON.stringify({ schemaVersion: 1, annotations: [note] }))[0].reviewStatus).toBe('needs_review');
    expect(() => parseNotes(JSON.stringify({ schemaVersion: 1, annotations: [{ ...note, geometry: { type: 'Polygon', coordinates: [[[0, 0], [1, 0], [1, 1], [2, 2]]] } }] }))).toThrow(/geometry/);
  });
});
describe('episode asset integrity and lifecycle', () => {
  async function asset() {
    vi.stubGlobal('crypto', webcrypto);
    const bytes = new TextEncoder().encode('synthetic media bytes');
    const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map((n) => n.toString(16).padStart(2, '0')).join('');
    const descriptor: EpisodeAsset = { id: 'sound', kind: 'audio', path: 'test/sound.mp3', sha256: hash, byteLength: bytes.length, attribution: 'Synthetic test', license: 'CC0-1.0', coordinates: [0, 0] };
    vi.stubGlobal('URL', { createObjectURL: vi.fn(() => 'blob:test'), revokeObjectURL: vi.fn() });
    return { descriptor, files: { 'test/sound.mp3': { mimeType: 'audio/mpeg', base64: btoa(String.fromCharCode(...bytes)) } } };
  }
  it('creates a media URL only after verifying the declared bytes and hash', async () => {
    const { descriptor, files } = await asset();
    expect((await loadAsset(descriptor, files, new AbortController().signal)).url).toBe('blob:test');
    await expect(loadAsset({ ...descriptor, sha256: '0'.repeat(64) }, files, new AbortController().signal)).rejects.toThrow(/integrity/);
    expect(URL.createObjectURL).toHaveBeenCalledTimes(1);
  });
  it('does not allocate URLs for cancelled or wrong-type assets', async () => {
    const { descriptor, files } = await asset(); const controller = new AbortController(); controller.abort();
    await expect(loadAsset(descriptor, files, controller.signal)).rejects.toThrow();
    files['test/sound.mp3'].mimeType = 'text/html';
    await expect(loadAsset(descriptor, files, new AbortController().signal)).rejects.toThrow(/type/);
    expect(URL.createObjectURL).not.toHaveBeenCalled();
  });
});
