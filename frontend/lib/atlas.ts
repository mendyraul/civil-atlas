import type {
  AtlasFeature,
  Confidence,
  ReviewStatus,
  SourceRecord,
  WorldPayload,
} from '../types/atlas';
import { sourceCatalog, world117 } from '../data/world117';

export const DEFAULT_YEAR = 117;
export const YEAR_MIN = -600;
export const YEAR_MAX = 1800;
export const NODE_VISIBILITY_ZOOM = 3.4;
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export function isActiveAtYear(
  feature: Pick<AtlasFeature, 'startYear' | 'endYear'>,
  year: number,
) {
  return feature.startYear <= year && feature.endYear >= year;
}

export function filterWorldByYear(world: WorldPayload, year: number): WorldPayload {
  return {
    year,
    civilizations: world.civilizations.filter((feature) => isActiveAtYear(feature, year)),
    nodes: world.nodes.filter((feature) => isActiveAtYear(feature, year)),
    routes: world.routes.filter((feature) => isActiveAtYear(feature, year)),
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

export async function fetchWorld(year = DEFAULT_YEAR): Promise<WorldPayload> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/world/${year}`, {
      cache: 'no-store',
    });
    if (!response.ok) {
      return filterWorldByYear(world117, year);
    }
    return (await response.json()) as WorldPayload;
  } catch {
    return filterWorldByYear(world117, year);
  }
}

export async function fetchCivilizations() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/civilizations`, {
      cache: 'no-store',
    });
    if (!response.ok) return world117.civilizations;
    return (await response.json()) as WorldPayload['civilizations'];
  } catch {
    return world117.civilizations;
  }
}

export async function fetchPlaces() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/places`, {
      cache: 'no-store',
    });
    if (!response.ok) return world117.nodes;
    return (await response.json()) as WorldPayload['nodes'];
  } catch {
    return world117.nodes;
  }
}

export async function fetchSources(): Promise<SourceRecord[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/sources`, {
      cache: 'no-store',
    });
    if (!response.ok) return sourceCatalog;
    return (await response.json()) as SourceRecord[];
  } catch {
    return sourceCatalog;
  }
}
