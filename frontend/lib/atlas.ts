import type {
  AtlasFeature,
  Confidence,
  HistoricalEvent,
  ReviewStatus,
  SourceRecord,
  WorldPayload,
} from '../types/atlas';
import { sourceCatalog, world117 as demoWorld117 } from '../data/demoWorld117';

export const DEFAULT_YEAR = 117;
export const YEAR_MIN = -600;
export const YEAR_MAX = 1800;
export const NODE_VISIBILITY_ZOOM = 3.4;
const configuredApiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
const developmentFallbackApiBaseUrl =
  process.env.NODE_ENV === 'development' ? 'http://localhost:8000' : '';

export const API_BASE_URL = (configuredApiBaseUrl || developmentFallbackApiBaseUrl).replace(
  /\/$/,
  '',
);
export const HAS_REMOTE_API = API_BASE_URL.length > 0;
export const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === 'true';
export const EVENT_PROXIMITY_WINDOW = 40;

function buildApiUrl(path: string) {
  return `${API_BASE_URL}${path}`;
}

export function isActiveAtYear(
  feature: Pick<AtlasFeature, 'startYear' | 'endYear'>,
  year: number,
) {
  return feature.startYear <= year && feature.endYear >= year;
}

export function isEventRelevantAtYear(
  event: Pick<HistoricalEvent, 'startYear' | 'endYear'>,
  year: number,
) {
  return event.startYear <= year + EVENT_PROXIMITY_WINDOW && event.endYear >= year - EVENT_PROXIMITY_WINDOW;
}

export function filterWorldByYear(world: WorldPayload, year: number): WorldPayload {
  return {
    year,
    civilizations: world.civilizations.filter((feature) => isActiveAtYear(feature, year)),
    nodes: world.nodes.filter((feature) => isActiveAtYear(feature, year)),
    routes: world.routes.filter((feature) => isActiveAtYear(feature, year)),
    layers: world.layers.filter((layer) => layer.validFromYear <= year && layer.validToYear >= year),
    relationships: world.relationships.filter(
      (relationship) =>
        relationship.validFromYear <= year && relationship.validToYear >= year,
    ),
    eras: world.eras.filter((era) => isActiveAtYear(era, year)),
    events: world.events.filter((event) => isEventRelevantAtYear(event, year)),
  };
}

export function formatYear(year: number) {
  if (year === 0) return '0';
  return year < 0 ? `${Math.abs(year)} BCE` : `${year} CE`;
}

export function evidenceTone(confidence: Confidence) {
  switch (confidence) {
    case 'high':
      return 'bg-emerald-100 text-emerald-800';
    case 'medium_high':
      return 'bg-teal-100 text-teal-800';
    case 'medium':
      return 'bg-amber-100 text-amber-800';
    case 'low':
      return 'bg-rose-100 text-rose-800';
  }
}

export function confidenceLabel(confidence: Confidence) {
  return confidence.replace('_', ' ');
}

export function reviewTone(reviewStatus: ReviewStatus) {
  switch (reviewStatus) {
    case 'reviewed':
      return 'bg-emerald-100 text-emerald-800';
    case 'seeded':
      return 'bg-sky-100 text-sky-800';
    case 'placeholder':
      return 'bg-rose-100 text-rose-800';
    case 'needs_review':
      return 'bg-violet-100 text-violet-800';
  }
}

export function reviewLabel(reviewStatus: ReviewStatus) {
  return reviewStatus.replace('_', ' ');
}

export function getFeatureById(world: WorldPayload, id?: string) {
  if (!id) return undefined;
  return [...world.civilizations, ...world.nodes, ...world.routes].find(
    (feature) => feature.id === id,
  );
}

export function featureBadgeTone(badge: string) {
  switch (badge) {
    case 'Approximate':
      return 'bg-amber-100 text-amber-900';
    case 'Source-reported':
      return 'bg-sky-100 text-sky-800';
    case 'Placeholder geometry':
      return 'bg-rose-100 text-rose-800';
    case 'Needs review':
      return 'bg-violet-100 text-violet-800';
    case 'Reviewed':
      return 'bg-emerald-100 text-emerald-800';
    default:
      return 'bg-slate-200 text-slate-800';
  }
}

export function relationshipTypeLabel(value: string) {
  return value.replace(/_/g, ' ');
}

export function interpretationLabel(value?: string) {
  if (!value) return 'Variant';
  return value;
}

async function fetchApi<T>(path: string): Promise<T> {
  if (!HAS_REMOTE_API) {
    throw new Error('Civil Atlas API is not configured');
  }
  const response = await fetch(buildApiUrl(path), { cache: 'no-store' });
  if (!response.ok) throw new Error(`Civil Atlas API returned ${response.status}`);
  return (await response.json()) as T;
}

export async function fetchWorld(year = DEFAULT_YEAR): Promise<WorldPayload> {
  if (DEMO_MODE) return filterWorldByYear(demoWorld117, year);
  return fetchApi<WorldPayload>(`/api/v1/world/${year}`);
}

export async function fetchCivilizations() {
  if (DEMO_MODE) return demoWorld117.civilizations;
  if (!HAS_REMOTE_API) return [];
  try { return await fetchApi<WorldPayload['civilizations']>('/api/v1/civilizations'); }
  catch { return []; }
}

export async function fetchPlaces() {
  if (DEMO_MODE) return demoWorld117.nodes;
  if (!HAS_REMOTE_API) return [];
  try { return await fetchApi<WorldPayload['nodes']>('/api/v1/places'); }
  catch { return []; }
}

export async function fetchSources(): Promise<SourceRecord[]> {
  if (DEMO_MODE) return sourceCatalog;
  if (!HAS_REMOTE_API) return [];
  try { return await fetchApi<SourceRecord[]>('/api/v1/sources'); }
  catch { return []; }
}
