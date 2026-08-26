'use client';

import { Suspense, lazy, useEffect, useMemo, useRef, useState } from 'react';
import { world117 as demoWorld117 } from '../../data/demoWorld117';
import { learningChapters } from '../../data/learningChapters';
import {
  API_BASE_URL,
  DEFAULT_YEAR,
  DEMO_MODE,
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

type DataState = 'live' | 'demo' | 'loading' | 'stale' | 'unavailable';

const emptyWorld: WorldPayload = { year: DEFAULT_YEAR, civilizations: [], nodes: [], routes: [], layers: [], relationships: [], eras: [], events: [] };

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
  const [baseWorld, setBaseWorld] = useState<WorldPayload>(DEMO_MODE ? demoWorld117 : emptyWorld);
  const [year, setYear] = useState(DEFAULT_YEAR);
  const [selectedId, setSelectedId] = useState<string>('roman-empire');
  const [zoom, setZoom] = useState(2.1);
  const [center, setCenter] = useState<[number, number]>([30, 25]);
  const [backendStatus, setBackendStatus] = useState<DataState>(DEMO_MODE ? 'demo' : 'loading');
  const [layers, setLayers] = useState<LayerVisibility>({
    extents: true,
    nodes: true,
    routes: true,
    sources: true,
  });
  const [filters, setFilters] = useState<FilterState>(emptyFilterState);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [pauseOnEvent, setPauseOnEvent] = useState(true);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [mode, setMode] = useState<'explore' | 'guided'>('explore');
  const [chapterId, setChapterId] = useState(learningChapters[0].id);
  const [stepId, setStepId] = useState(learningChapters[0].steps[0].id);
  const skipFirstUrlSyncRef = useRef(true);

  useEffect(() => {
    const query = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => { setReducedMotion(query.matches); if (query.matches) setIsPlaying(false); };
    update();
    query.addEventListener('change', update);
    return () => query.removeEventListener('change', update);
  }, []);

  useEffect(() => {
    if (DEMO_MODE) return;
    if (!HAS_REMOTE_API) { setBackendStatus('unavailable'); return; }

    let cancelled = false;

    async function loadWorld() {
      setBackendStatus((current) => current === 'live' ? 'live' : 'loading');
      try {
        const [worldResponse, healthResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/api/v1/world/${DEFAULT_YEAR}`, { cache: 'no-store' }),
          fetch(`${API_BASE_URL}/api/health`, { cache: 'no-store' }),
        ]);
        if (!worldResponse.ok || !healthResponse.ok) throw new Error('API unavailable');
        const payload = (await worldResponse.json()) as WorldPayload;
        const health = (await healthResponse.json()) as { data?: { updated_at?: string } };
        const updatedAt = health.data?.updated_at ? Date.parse(health.data.updated_at) : NaN;
        const stale = Number.isFinite(updatedAt) && Date.now() - updatedAt > 24 * 60 * 60 * 1000;
        if (!cancelled) { setBaseWorld(payload); setBackendStatus(stale ? 'stale' : 'live'); }
      } catch {
        if (!cancelled) setBackendStatus((current) => current === 'live' || current === 'stale' ? 'stale' : 'unavailable');
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
    const urlZoom = Number(params.get('z')); const longitude = Number(params.get('lng')); const latitude = Number(params.get('lat'));
    if (Number.isFinite(urlZoom)) setZoom(urlZoom);
    if (Number.isFinite(longitude) && Number.isFinite(latitude)) setCenter([longitude, latitude]);
    const encodedLayers = params.get('layers');
    if (encodedLayers) setLayers((current) => ({ ...current, ...Object.fromEntries(encodedLayers.split(',').map((key) => [key, true])), ...Object.fromEntries(Object.keys(current).filter((key) => !encodedLayers.split(',').includes(key)).map((key) => [key, false])) }));
    setFilters({ confidence: (params.get('confidence')?.split(',').filter(Boolean) ?? []) as Confidence[], reviewStatus: (params.get('review')?.split(',').filter(Boolean) ?? []) as ReviewStatus[], layerTypes: params.get('types')?.split(',').filter(Boolean) ?? [] });
    const urlChapter = learningChapters.find((chapter) => chapter.id === params.get('chapter'));
    const urlStep = urlChapter?.steps.find((step) => step.id === params.get('step'));
    if (urlChapter && urlStep) {
      setMode('guided'); setChapterId(urlChapter.id); setStepId(urlStep.id);
    }
  }, []);

  // Research mode: keep the URL in sync with year + selection so any view is shareable.
  useEffect(() => {
    if (skipFirstUrlSyncRef.current) {
      skipFirstUrlSyncRef.current = false;
      return;
    }
    const params = new URLSearchParams(window.location.search);
    params.set('y', String(year));
    if (selectedId) {
      params.set('sel', selectedId);
    }
    params.set('z', zoom.toFixed(2)); params.set('lng', center[0].toFixed(3)); params.set('lat', center[1].toFixed(3));
    params.set('layers', Object.entries(layers).filter(([, active]) => active).map(([key]) => key).join(','));
    if (filters.confidence.length) params.set('confidence', filters.confidence.join(',')); else params.delete('confidence');
    if (filters.reviewStatus.length) params.set('review', filters.reviewStatus.join(',')); else params.delete('review');
    if (filters.layerTypes.length) params.set('types', filters.layerTypes.join(',')); else params.delete('types');
    if (mode === 'guided') { params.set('chapter', chapterId); params.set('step', stepId); }
    const query = params.toString();
    window.history.replaceState(null, '', query ? `?${query}` : window.location.pathname);
  }, [year, selectedId, zoom, center, layers, filters, mode, chapterId, stepId]);

  // Workstream D: timeline autoplay.
  useEffect(() => {
    if (!isPlaying || reducedMotion) {
      return;
    }
    const intervalId = window.setInterval(() => {
      setYear((current) => {
        const proposed = current + PLAYBACK_STEP_YEARS;
        const crossedEvent = baseWorld.events.filter((event) => event.startYear > current && event.startYear <= proposed).sort((a, b) => a.startYear - b.startYear)[0];
        const next = pauseOnEvent && crossedEvent ? crossedEvent.startYear : proposed;
        if (crossedEvent && pauseOnEvent) setIsPlaying(false);
        if (next >= YEAR_MAX) {
          setIsPlaying(false);
          return YEAR_MAX;
        }
        return next;
      });
    }, PLAYBACK_TICK_MS / playbackSpeed);
    return () => window.clearInterval(intervalId);
  }, [isPlaying, playbackSpeed, pauseOnEvent, reducedMotion, baseWorld.events]);

  function stepTimeline(direction: -1 | 1, target: 'event' | 'era') {
    setIsPlaying(false);
    const points = (target === 'event' ? baseWorld.events.flatMap((event) => [event.startYear, event.endYear]) : baseWorld.eras.flatMap((era) => [era.startYear, era.endYear])).filter((value, index, values) => values.indexOf(value) === index).sort((a, b) => a - b);
    const destination = direction > 0 ? points.find((point) => point > year) : [...points].reverse().find((point) => point < year);
    if (destination !== undefined) setYear(destination);
  }

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement || event.target instanceof HTMLSelectElement) return;
      if (event.code === 'Space') { event.preventDefault(); togglePlay(); }
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') { event.preventDefault(); stepTimeline(event.key === 'ArrowLeft' ? -1 : 1, event.shiftKey ? 'era' : 'event'); }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  });

  function togglePlay() {
    if (reducedMotion) return;
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
        chapters={learningChapters}
        chapterId={chapterId}
        mode={mode}
        stepId={stepId}
        onModeChange={setMode}
        onLessonStep={(nextChapterId, nextStepId) => {
          const chapter = learningChapters.find((item) => item.id === nextChapterId);
          const step = chapter?.steps.find((item) => item.id === nextStepId);
          if (!step) return;
          setChapterId(nextChapterId); setStepId(nextStepId); setYear(step.year);
          if (step.selectedEntityId) setSelectedId(step.selectedEntityId);
          setLayers({ extents: false, nodes: false, routes: false, sources: false, ...Object.fromEntries(step.visibleLayers.map((layer) => [layer, true])) });
        }}
        backendStatus={backendStatus}
        confidenceCounts={confidenceCounts}
        detailWorld={activeWorld}
        eras={baseWorld.eras}
        events={baseWorld.events}
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
              initialCenter={center}
              initialZoom={zoom}
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
              onCenterChange={setCenter}
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
        playbackSpeed={playbackSpeed}
        pauseOnEvent={pauseOnEvent}
        reducedMotion={reducedMotion}
        onPlaybackSpeedChange={setPlaybackSpeed}
        onPauseOnEventChange={setPauseOnEvent}
        onStep={stepTimeline}
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
