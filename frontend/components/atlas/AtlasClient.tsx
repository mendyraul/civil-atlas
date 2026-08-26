'use client';

import { Suspense, lazy, useEffect, useMemo, useRef, useState } from 'react';
import { world117 } from '../../data/world117';
import {
  API_BASE_URL,
  DEFAULT_YEAR,
  HAS_REMOTE_API,
  YEAR_MAX,
  YEAR_MIN,
  filterWorldByYear,
  getFeatureById,
} from '../../lib/atlas';
import type { AtlasFeature, Confidence, ReviewStatus, WorldPayload } from '../../types/atlas';
import { AtlasPage } from './AtlasPage';
import { SiteShell } from './SiteShell';

const LazyAtlasMap = lazy(async () => {
  const module = await import('../map/AtlasMap');
  return { default: module.AtlasMap };
});

type LayerVisibility = {
  extents: boolean;
  nodes: boolean;
  routes: boolean;
  sources: boolean;
};

type FilterState = {
  confidence: Confidence[];
  layerTypes: string[];
  reviewStatus: ReviewStatus[];
};

const emptyFilterState: FilterState = {
  confidence: [],
  layerTypes: [],
  reviewStatus: [],
};

// Workstream D: autoplay advances the year ~55 years/second (5 years every 90ms).
const PLAYBACK_TICK_MS = 90;
const PLAYBACK_STEP_YEARS = 5;

function toggleValue<T extends string>(values: T[], value: T) {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}

function layerTypeValue(feature: AtlasFeature) {
  if (feature.kind === 'civilization') {
    return `civilization:${feature.civilizationType}`;
  }
  if (feature.kind === 'node') {
    return `node:${feature.role}`;
  }
  return `route:${feature.routeKind}`;
}

function layerTypeLabel(value: string) {
  const [group, raw] = value.split(':');
  const label = raw.replace(/_/g, ' ');
  if (group === 'civilization') return `Polity: ${label}`;
  if (group === 'node') return `Place: ${label}`;
  return `Route: ${label}`;
}

export function AtlasClient() {
  const [baseWorld, setBaseWorld] = useState<WorldPayload>(world117);
  const [year, setYear] = useState(DEFAULT_YEAR);
  const [selectedId, setSelectedId] = useState<string>('roman-empire');
  const [zoom, setZoom] = useState(2.1);
  const [backendStatus, setBackendStatus] = useState<'seed' | 'live'>('seed');
  const [layers, setLayers] = useState<LayerVisibility>({
    extents: true,
    nodes: true,
    routes: true,
    sources: true,
  });
  const [filters, setFilters] = useState<FilterState>(emptyFilterState);
  const [isPlaying, setIsPlaying] = useState(false);
  const skipFirstUrlSyncRef = useRef(true);

  useEffect(() => {
    if (!HAS_REMOTE_API) {
      return;
    }

    let cancelled = false;

    async function loadWorld() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/world/${DEFAULT_YEAR}`, {
          cache: 'no-store',
        });
        if (!response.ok) {
          return;
        }
        const payload = (await response.json()) as WorldPayload;
        if (!cancelled) {
          setBaseWorld(payload);
          setBackendStatus('live');
        }
      } catch {
        // Seed fallback is intentional for the MVP.
      }
    }

    void loadWorld();
    return () => {
      cancelled = true;
    };
  }, []);

  // Research mode: hydrate view state from the URL on load (shareable views).
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlYear = Number(params.get('y'));
    if (Number.isFinite(urlYear) && urlYear >= YEAR_MIN && urlYear <= YEAR_MAX) {
      setYear(urlYear);
    }
    const urlSelected = params.get('sel');
    if (urlSelected) {
      setSelectedId(urlSelected);
    }
  }, []);

  // Research mode: keep the URL in sync with year + selection so any view is shareable.
  useEffect(() => {
    if (skipFirstUrlSyncRef.current) {
      skipFirstUrlSyncRef.current = false;
      return;
    }
    const params = new URLSearchParams();
    params.set('y', String(year));
    if (selectedId) {
      params.set('sel', selectedId);
    }
    const query = params.toString();
    window.history.replaceState(null, '', query ? `?${query}` : window.location.pathname);
  }, [year, selectedId]);

  // Workstream D: timeline autoplay.
  useEffect(() => {
    if (!isPlaying) {
      return;
    }
    const intervalId = window.setInterval(() => {
      setYear((current) => {
        const next = current + PLAYBACK_STEP_YEARS;
        if (next >= YEAR_MAX) {
          setIsPlaying(false);
          return YEAR_MAX;
        }
        return next;
      });
    }, PLAYBACK_TICK_MS);
    return () => window.clearInterval(intervalId);
  }, [isPlaying]);

  function togglePlay() {
    setIsPlaying((current) => {
      // Restart from the beginning if we're paused at the end of the timeline.
      if (!current && year >= YEAR_MAX) {
        setYear(YEAR_MIN);
      }
      return !current;
    });
  }

  const activeWorld = useMemo(() => filterWorldByYear(baseWorld, year), [baseWorld, year]);
  const featuresByLayerType = useMemo(() => {
    const allFeatures: AtlasFeature[] = [
      ...activeWorld.civilizations,
      ...activeWorld.nodes,
      ...activeWorld.routes,
    ];
    return allFeatures.reduce<Map<string, number>>((counts, feature) => {
      const key = layerTypeValue(feature);
      counts.set(key, (counts.get(key) ?? 0) + 1);
      return counts;
    }, new Map());
  }, [activeWorld]);
  const layerTypeOptions = useMemo(
    () =>
      Array.from(featuresByLayerType.entries())
        .map(([value, count]) => ({
          count,
          group: value.split(':', 1)[0] as 'civilization' | 'node' | 'route',
          label: layerTypeLabel(value),
          value,
        }))
        .sort((left, right) => left.label.localeCompare(right.label)),
    [featuresByLayerType],
  );
  const reviewCounts = useMemo(
    () =>
      ({
        placeholder: [...activeWorld.civilizations, ...activeWorld.nodes, ...activeWorld.routes].filter(
          (feature) => feature.reviewStatus === 'placeholder',
        ).length,
        seeded: [...activeWorld.civilizations, ...activeWorld.nodes, ...activeWorld.routes].filter(
          (feature) => feature.reviewStatus === 'seeded',
        ).length,
        needs_review: [...activeWorld.civilizations, ...activeWorld.nodes, ...activeWorld.routes].filter(
          (feature) => feature.reviewStatus === 'needs_review',
        ).length,
        reviewed: [...activeWorld.civilizations, ...activeWorld.nodes, ...activeWorld.routes].filter(
          (feature) => feature.reviewStatus === 'reviewed',
        ).length,
      }) satisfies Record<ReviewStatus, number>,
    [activeWorld],
  );
  const confidenceCounts = useMemo(
    () =>
      ({
        low: [...activeWorld.civilizations, ...activeWorld.nodes, ...activeWorld.routes].filter(
          (feature) => feature.confidence === 'low',
        ).length,
        medium: [...activeWorld.civilizations, ...activeWorld.nodes, ...activeWorld.routes].filter(
          (feature) => feature.confidence === 'medium',
        ).length,
        medium_high: [...activeWorld.civilizations, ...activeWorld.nodes, ...activeWorld.routes].filter(
          (feature) => feature.confidence === 'medium_high',
        ).length,
        high: [...activeWorld.civilizations, ...activeWorld.nodes, ...activeWorld.routes].filter(
          (feature) => feature.confidence === 'high',
        ).length,
      }) satisfies Record<Confidence, number>,
    [activeWorld],
  );
  const filteredWorld = useMemo(() => {
    const matchesFeature = (feature: AtlasFeature) => {
      if (filters.layerTypes.length > 0 && !filters.layerTypes.includes(layerTypeValue(feature))) {
        return false;
      }
      if (filters.reviewStatus.length > 0 && !filters.reviewStatus.includes(feature.reviewStatus)) {
        return false;
      }
      if (filters.confidence.length > 0 && !filters.confidence.includes(feature.confidence)) {
        return false;
      }
      return true;
    };

    return {
      ...activeWorld,
      civilizations: activeWorld.civilizations.filter(matchesFeature),
      nodes: activeWorld.nodes.filter(matchesFeature),
      routes: activeWorld.routes.filter(matchesFeature),
    };
  }, [activeWorld, filters.confidence, filters.layerTypes, filters.reviewStatus]);
  const visibleWorld = useMemo(
    () => ({
      ...filteredWorld,
      civilizations: layers.extents ? filteredWorld.civilizations : [],
      nodes: layers.nodes ? filteredWorld.nodes : [],
      routes: layers.routes ? filteredWorld.routes : [],
    }),
    [filteredWorld, layers.extents, layers.nodes, layers.routes],
  );
  const selectedFeature = useMemo(
    () => getFeatureById(activeWorld, selectedId) ?? getFeatureById(baseWorld, selectedId),
    [activeWorld, baseWorld, selectedId],
  );
  const isSelectedFeatureFilteredOut = useMemo(() => {
    if (!selectedFeature) return false;
    return getFeatureById(visibleWorld, selectedFeature.id) === undefined;
  }, [selectedFeature, visibleWorld]);
  const highlightedIds = useMemo(
    () =>
      layers.sources
        ? selectedFeature?.evidence.map((record) => record.id) ?? []
        : [],
    [layers.sources, selectedFeature],
  );
  const filterCount =
    filters.layerTypes.length + filters.reviewStatus.length + filters.confidence.length;

  function toggleLayer(layer: keyof LayerVisibility) {
    setLayers((current) => ({ ...current, [layer]: !current[layer] }));
  }

  function toggleLayerType(value: string) {
    setFilters((current) => ({ ...current, layerTypes: toggleValue(current.layerTypes, value) }));
  }

  function toggleReviewStatus(value: ReviewStatus) {
    setFilters((current) => ({
      ...current,
      reviewStatus: toggleValue(current.reviewStatus, value),
    }));
  }

  function toggleConfidence(value: Confidence) {
    setFilters((current) => ({
      ...current,
      confidence: toggleValue(current.confidence, value),
    }));
  }

  return (
    <SiteShell
      title="Civil Atlas"
      subtitle="Main atlas interface"
    >
      <AtlasPage
        backendStatus={backendStatus}
        confidenceCounts={confidenceCounts}
        detailWorld={activeWorld}
        eras={activeWorld.eras}
        events={activeWorld.events}
        filterCount={filterCount}
        isPlaying={isPlaying}
        isSelectedFeatureFilteredOut={isSelectedFeatureFilteredOut}
        layerTypeOptions={layerTypeOptions}
        layers={layers}
        map={
          <Suspense
            fallback={
              <div className="grid h-[72vh] min-h-[560px] place-items-center text-lg tracking-[0.04em] text-slate-500">
                Loading atlas...
              </div>
            }
          >
            <LazyAtlasMap
              civilizations={visibleWorld.civilizations}
              civilizationLayers={visibleWorld.layers.filter((layer) =>
                visibleWorld.civilizations.some((item) => item.id === layer.civilizationId),
              )}
              evidenceIds={highlightedIds}
              nodes={visibleWorld.nodes}
              routes={visibleWorld.routes}
              selectedId={selectedId}
              showEvidence={layers.sources}
              showExtents={layers.extents}
              showNodes={layers.nodes}
              showRoutes={layers.routes}
              onCivilizationSelect={setSelectedId}
              onNodeSelect={setSelectedId}
              onRouteSelect={setSelectedId}
              onZoomChange={setZoom}
            />
          </Suspense>
        }
        onCivilizationSelect={setSelectedId}
        onConfidenceToggle={toggleConfidence}
        onLayerTypeToggle={toggleLayerType}
        onResetFilters={() => setFilters(emptyFilterState)}
        onReviewStatusToggle={toggleReviewStatus}
        onToggleLayer={toggleLayer}
        onTogglePlay={togglePlay}
        onYearChange={setYear}
        reviewCounts={reviewCounts}
        selectedConfidence={filters.confidence}
        selectedFeature={selectedFeature}
        selectedId={selectedId}
        selectedLayerTypes={filters.layerTypes}
        selectedReviewStatus={filters.reviewStatus}
        world={filteredWorld}
        year={year}
        zoom={zoom}
      />
    </SiteShell>
  );
}
