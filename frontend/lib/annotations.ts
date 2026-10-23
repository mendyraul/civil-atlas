import type { GeoJSONPosition, MapAnnotation } from '../types/atlas';
import { normalizeApiPayload } from './atlas';

export function validateAnnotation(value: unknown): MapAnnotation {
  const item = normalizeApiPayload<MapAnnotation>(value);
  if (!item || typeof item.id !== 'string' || !item.id || item.id.length > 160 || typeof item.title !== 'string' || !item.title.trim() || item.title.length > 200 || typeof item.note !== 'string' || item.note.length > 10000 || !Number.isInteger(item.validFromYear) || !Number.isInteger(item.validToYear) || item.validFromYear < -600 || item.validToYear > 1800 || item.validFromYear > item.validToYear) throw Error('Invalid annotation title, note, or date range.');
  if (!Array.isArray(item.sourceRecordIds) || item.sourceRecordIds.length > 100 || item.sourceRecordIds.some((id) => typeof id !== 'string') || !['explanation', 'territory'].includes(item.kind) || !['needs_review', 'reviewed', 'rejected'].includes(item.reviewStatus) || !['low', 'medium', 'medium_high', 'high'].includes(item.confidence)) throw Error('Invalid annotation metadata.');
  if (item.kind === 'territory' && (!item.boundaryLayerId || item.geometry)) throw Error('Territory must reference a sourced boundary.');
  if (item.boundaryLayerId && typeof item.boundaryLayerId !== 'string') throw Error('Invalid boundary reference.');
  if (!item.geometry && !item.boundaryLayerId) throw Error('Annotation needs geometry.');
  if (item.geometry) {
    let count = 0;
    const point = (value: unknown): value is GeoJSONPosition => Array.isArray(value) && value.length === 2 && value.every((n) => typeof n === 'number' && Number.isFinite(n)) && Math.abs(value[0]) <= 180 && Math.abs(value[1]) <= 90 && ++count <= 50000;
    const line = (value: unknown, ring = false) => Array.isArray(value) && value.length >= (ring ? 4 : 2) && value.every(point) && (!ring || JSON.stringify(value[0]) === JSON.stringify(value.at(-1)));
    const polygon = (value: unknown): boolean => Array.isArray(value) && value.length > 0 && value.every((r) => line(r, true));
    const geometry = item.geometry;
    if (!(geometry.type === 'Point' ? point(geometry.coordinates) : geometry.type === 'LineString' ? line(geometry.coordinates) : geometry.type === 'Polygon' ? polygon(geometry.coordinates) : geometry.type === 'MultiPolygon' && Array.isArray(geometry.coordinates) && geometry.coordinates.length > 0 && geometry.coordinates.every(polygon))) throw Error('Invalid annotation geometry.');
  }
  return item;
}

export function parseNotes(text: string): MapAnnotation[] {
  if (new TextEncoder().encode(text).length > 8 * 1024 * 1024) throw Error('Annotation file exceeds 8 MiB.');
  const data = JSON.parse(text);
  if (data.schemaVersion !== 1 || !Array.isArray(data.annotations) || data.annotations.length > 1000) throw Error('Unsupported annotation file.');
  const items = data.annotations.map(validateAnnotation).map((item: MapAnnotation) => ({ ...item, reviewStatus: 'needs_review' as const, kind: 'explanation' as const }));
  if (new Set(items.map((item: MapAnnotation) => item.id)).size !== items.length) throw Error('Duplicate annotation IDs.');
  return items;
}
export function downloadJson(name: string, data: unknown) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
  const link = document.createElement('a'); link.href = url; link.download = name; link.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function database(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('civil-atlas-personal', 1);
    request.onupgradeneeded = () => request.result.createObjectStore('notes');
    request.onerror = () => reject(request.error); request.onblocked = () => reject(Error('Storage blocked'));
    request.onsuccess = () => resolve(request.result);
  });
}
export async function readNotes(): Promise<MapAnnotation[]> {
  const db = await database();
  try { return await new Promise((resolve, reject) => { const tx = db.transaction('notes', 'readonly'); const r = tx.objectStore('notes').get('annotations'); r.onsuccess = () => { try { resolve((r.result ?? []).map(validateAnnotation)); } catch (error) { reject(error); } }; r.onerror = () => reject(r.error); }); } finally { db.close(); }
}
export async function writeNotes(notes: MapAnnotation[]) {
  const db = await database();
  try { await new Promise<void>((resolve, reject) => { const tx = db.transaction('notes', 'readwrite'); tx.objectStore('notes').put(notes, 'annotations'); tx.oncomplete = () => resolve(); tx.onerror = () => reject(tx.error); tx.onabort = () => reject(tx.error); }); } finally { db.close(); }
}
