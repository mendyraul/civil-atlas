import type { EpisodeAsset, EpisodePack } from '../types/atlas';
import { normalizeApiPayload } from './atlas';
import { validateAnnotation } from './annotations';
export type EpisodeBundle = { schemaVersion: 1; pack: EpisodePack; files?: Record<string, { mimeType: string; base64: string }> };
const maxAsset = 8 * 1024 * 1024, maxBundle = 32 * 1024 * 1024;
function strings(value: unknown): value is string[] { return Array.isArray(value) && value.length <= 100 && value.every((s) => typeof s === 'string' && s.length <= 200); }
export function validateEpisode(value: unknown): EpisodePack {
  const p = normalizeApiPayload<EpisodePack>(value);
  if (!p || p.schemaVersion !== 1 || typeof p.id !== 'string' || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(p.id) || typeof p.title !== 'string' || !p.title.trim() || p.title.length > 200 || typeof p.summary !== 'string' || p.summary.length > 10000 || typeof p.datasetVersion !== 'string' || !p.datasetVersion || typeof p.attribution !== 'string' || !p.attribution || p.license !== 'ODbL-1.0' || !['needs_review', 'reviewed', 'rejected'].includes(p.reviewStatus)) throw Error('Invalid episode metadata.');
  if (!Array.isArray(p.steps) || !p.steps.length || p.steps.length > 100 || !Array.isArray(p.annotations) || p.annotations.length > 1000 || !Array.isArray(p.assets) || p.assets.length > 100) throw Error('Invalid episode collections.');
  p.annotations = p.annotations.map(validateAnnotation);
  for (const group of [p.steps, p.annotations, p.assets]) if (group.some((i) => typeof i.id !== 'string' || !i.id) || new Set(group.map((i) => i.id)).size !== group.length) throw Error('Duplicate or missing episode IDs.');
  for (const asset of p.assets) {
    if (typeof asset.path !== 'string' || !/^[A-Za-z0-9_-]+(?:\/[A-Za-z0-9_.-]+)+$/.test(asset.path) || asset.path.split('/').some((part) => part === '..' || part === '.') || typeof asset.attribution !== 'string' || !asset.attribution || !['CC0-1.0', 'PDDL-1.0', 'CC-BY-3.0', 'CC-BY-4.0', 'ODbL-1.0'].includes(asset.license) || !/^[a-f0-9]{64}$/.test(asset.sha256) || !Number.isInteger(asset.byteLength) || asset.byteLength <= 0 || asset.byteLength > maxAsset) throw Error('Invalid asset path, attribution, license, or integrity metadata.');
    const extensions = { image: /\.png$/i, audio: /\.(mp3|ogg|wav)$/i, video: /\.(mp4|webm)$/i };
    if (!extensions[asset.kind]?.test(asset.path)) throw Error('Unsupported asset format.');
    if (asset.kind === 'image') { const b = asset.bounds; if (!b || b.length !== 4 || !b.every(Number.isFinite) || !(-180 <= b[0] && b[0] < b[2] && b[2] <= 180 && -85 <= b[1] && b[1] < b[3] && b[3] <= 85)) throw Error('Image needs geographic bounds.'); }
    else if (!asset.coordinates || asset.coordinates.length !== 2 || !asset.coordinates.every(Number.isFinite) || Math.abs(asset.coordinates[0]) > 180 || Math.abs(asset.coordinates[1]) > 90) throw Error('Media needs a geographic anchor.');
  }
  for (const step of p.steps) {
    const c = step.camera;
    if (typeof step.title !== 'string' || !step.title || step.title.length > 200 || typeof step.narrative !== 'string' || step.narrative.length > 10000 || !Number.isInteger(step.year) || step.year < -600 || step.year > 1800 || !c || !Array.isArray(c.center) || c.center.length !== 2 || !c.center.every(Number.isFinite) || Math.abs(c.center[0]) > 180 || Math.abs(c.center[1]) > 85 || !Number.isFinite(c.zoom) || c.zoom < 0 || c.zoom > 20 || !Number.isFinite(step.holdSeconds) || step.holdSeconds < 2 || step.holdSeconds > 120 || !strings(step.entityIds) || !strings(step.layerIds) || !strings(step.sourceRecordIds) || !strings(step.annotationIds) || !strings(step.assetIds)) throw Error('Invalid episode step.');
    if (c.bearing !== undefined && (!Number.isFinite(c.bearing) || Math.abs(c.bearing) > 180) || c.pitch !== undefined && (!Number.isFinite(c.pitch) || c.pitch < 0 || c.pitch > 60)) throw Error('Invalid camera orientation.');
    if (step.annotationIds.some((id) => !p.annotations.some((a) => a.id === id)) || step.assetIds.some((id) => !p.assets.some((a) => a.id === id)) || step.assetIds.length > 8 || p.assets.filter((a) => step.assetIds.includes(a.id)).reduce((n, a) => n + a.byteLength, 0) > maxBundle) throw Error('Step references missing or oversized assets.');
  }
  return p;
}
export function parseEpisode(text: string): EpisodeBundle {
  if (new TextEncoder().encode(text).length > maxBundle) throw Error('Episode import exceeds 32 MiB.');
  const raw = JSON.parse(text), pack = validateEpisode(raw.pack ?? raw);
  if (raw.pack && raw.schemaVersion !== 1) throw Error('Unsupported bundle version.');
  const files = raw.pack ? raw.files : undefined;
  if (files !== undefined && (!files || typeof files !== 'object' || Array.isArray(files) || Object.keys(files).some((path) => !pack.assets.some((a) => a.path === path)))) throw Error('Bundle contains undeclared assets.');
  return { schemaVersion: 1, pack, files };
}
export type LoadedAsset = { asset: EpisodeAsset; url: string };
export async function loadAsset(asset: EpisodeAsset, files: EpisodeBundle['files'], signal: AbortSignal): Promise<LoadedAsset> {
  const supplied = files?.[asset.path];
  let bytes: Uint8Array;
  let mime: string;
  if (supplied) {
    if (typeof supplied.base64 !== 'string' || supplied.base64.length > maxAsset * 1.4 || typeof supplied.mimeType !== 'string') throw Error('Invalid bundled asset.');
    const data = atob(supplied.base64); bytes = Uint8Array.from(data, (c) => c.charCodeAt(0)); mime = supplied.mimeType;
  } else {
    const response = await fetch(`/episode-assets/${asset.path}`, { signal, credentials: 'omit', redirect: 'error' });
    if (!response.ok || !response.body) throw Error('An episode asset is unavailable.');
    mime = response.headers.get('Content-Type')?.split(';')[0] ?? '';
    const reader = response.body.getReader(); const chunks: Uint8Array[] = []; let length = 0;
    try { while (true) { const next = await reader.read(); if (next.done) break; length += next.value.length; if (length > asset.byteLength || length > maxAsset) throw Error('Asset exceeds its declared size.'); chunks.push(next.value); } } catch (error) { await reader.cancel(); throw error; }
    bytes = new Uint8Array(length); let offset = 0; for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
  }
  const allowed = { image: ['image/png'], audio: ['audio/mpeg', 'audio/ogg', 'audio/wav', 'audio/x-wav'], video: ['video/mp4', 'video/webm'] };
  if (!allowed[asset.kind].includes(mime) || bytes.length !== asset.byteLength) throw Error('Asset type or length does not match the manifest.');
  if (asset.kind === 'image') {
    if (bytes.length < 24 || [...bytes.slice(0, 8)].join(',') !== '137,80,78,71,13,10,26,10') throw Error('Invalid PNG image.');
    const view = new DataView(bytes.buffer as ArrayBuffer); const w = view.getUint32(16), h = view.getUint32(20);
    if (!w || !h || w > 4096 || h > 4096) throw Error('PNG dimensions exceed 4096 pixels.');
  }
  const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes.buffer as ArrayBuffer))].map((n) => n.toString(16).padStart(2, '0')).join('');
  if (digest !== asset.sha256) throw Error('Asset integrity check failed.');
  const blob = new Blob([bytes.buffer as ArrayBuffer], { type: mime });
  if (asset.kind === 'image') { const bitmap = await createImageBitmap(blob); bitmap.close(); }
  signal.throwIfAborted();
  return { asset, url: URL.createObjectURL(blob) };
}
