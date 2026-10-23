'use client';

import { Suspense, lazy, useEffect, useMemo, useState } from 'react';
import { useAtlasData } from './hooks/useAtlasData';
import { availableLayers, visibleBoundaryLayers, isCliopatria } from '../../lib/research';
import { AnnotationNotebook, usePersonalNotes, type DrawMode } from '../research/AnnotationNotebook';
import { ResearchWorkbench } from '../research/ResearchWorkbench';
import { LayerStatusPanel } from '../research/LayerStatusPanel';
import { EpisodePlayer } from '../episodes/EpisodePlayer';
import type { LoadedAsset } from '../../lib/episodes';
import { learningChapters } from '../../data/learningChapters';
import {
  DEFAULT_YEAR,
  YEAR_MAX,
  YEAR_MIN,
  getFeatureById,
} from '../../lib/atlas';
import type { EpisodePack, MapAnnotation, GeoJSONPosition, AtlasCamera, AtlasFeature, Confidence, ReviewStatus } from '../../types/atlas';
import { AtlasPage } from './AtlasPage';
import { SiteShell } from './SiteShell';

const LazyAtlasMap = lazy(async () => {
  const atlasMapModule = await import('../map/AtlasMap');
  return { default: atlasMapModule.AtlasMap };
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

// Advance in readable steps and wait for each year to finish loading.
const PLAYBACK_TICK_MS = 700;
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
  const [year, setYear] = useState(DEFAULT_YEAR);
  const [selectedId, setSelectedId] = useState<string>('');
  const [zoom, setZoom] = useState(1.8);
  const [center, setCenter] = useState<[number, number]>([30, 25]);
  const [ready, setReady] = useState(false);
  const { world: baseWorld, status: backendStatus, eras, events, sources, catalogFailed, reload } = useAtlasData(year, ready);
  const [camera, setCamera] = useState<AtlasCamera>({ center: [30, 25], zoom: 1.8, bearing: 0, pitch: 0 });
  const [cameraCommand, setCameraCommand] = useState<AtlasCamera | undefined>({ center: [30, 25], zoom: 1.8, bearing: 0, pitch: 0 });
  const [showModernBorders, setShowModernBorders] = useState(true);
  const [boundaryChoices, setBoundaryChoices] = useState<Record<string, boolean>>({});
  const [panel, setPanel] = useState<'layers' | 'details' | 'notes' | 'research' | 'episodes' | 'status' | null>(null);
  const notebook = usePersonalNotes();
  const [drawMode, setDrawMode] = useState<DrawMode | 'Rectangle' | null>(null);
  const [drawPoints, setDrawPoints] = useState<GeoJSONPosition[]>([]);
  const [bounds, setBounds] = useState<[number, number, number, number]>([-180, -85, 180, 85]);
  const [rectangle, setRectangle] = useState<[number, number, number, number] | null>(null);
  const [episodeStopToken, setEpisodeStopToken] = useState(0);
  const [episodeEntityIds, setEpisodeEntityIds] = useState<string[] | null>(null);
  const [episodeLayerIds, setEpisodeLayerIds] = useState<string[] | null>(null);
  const [episodeNotes, setEpisodeNotes] = useState<MapAnnotation[]>([]);
  const [episodeAssets, setEpisodeAssets] = useState<LoadedAsset[]>([]);
  function cancelDrawing() { setDrawMode(null); setDrawPoints([]); }
  function addDrawPoint(point: GeoJSONPosition) {
    const next = drawMode === 'Point' ? [point] : [...drawPoints, point];
    if (drawMode === 'Rectangle' && next.length >= 2) {
      const [a, b] = next; const west = Math.min(a[0], b[0]), east = Math.max(a[0], b[0]);
      setRectangle([east - west > 180 ? east : west, Math.min(a[1], b[1]), east - west > 180 ? west : east, Math.max(a[1], b[1])]);
      setDrawMode(null); setPanel('research'); setDrawPoints([]); return;
    }
    setDrawPoints(next.slice(0, 1000));
  }
  const mapNotes = useMemo(() => {
    const visible = [...notebook.notes, ...episodeNotes].filter((note) => note.validFromYear <= year && note.validToYear >= year);
    for (const { asset } of episodeAssets) if (asset.coordinates) visible.push({ id: `media-${asset.id}`, title: `Media: ${asset.attribution}`, note: asset.license, validFromYear: year, validToYear: year, sourceRecordIds: [], kind: 'explanation', reviewStatus: 'needs_review', confidence: 'low', geometry: { type: 'Point', coordinates: asset.coordinates } });
    if (drawPoints.length) visible.push({ id: 'personal-drawing-preview', title: 'Unsaved personal sketch', note: '', validFromYear: year, validToYear: year, sourceRecordIds: [], kind: 'explanation', reviewStatus: 'needs_review', confidence: 'low', geometry: drawPoints.length === 1 ? { type: 'Point', coordinates: drawPoints[0] } : { type: 'LineString', coordinates: drawPoints } });
    return visible;
  }, [notebook.notes, episodeNotes, episodeAssets, year, drawPoints]);
  const imageOverlays = useMemo(() => episodeAssets.flatMap(({ asset, url }) => asset.kind === 'image' && asset.bounds ? [{ id: asset.id, url, bounds: asset.bounds }] : []), [episodeAssets]);
  function applyEpisodeStep(pack: EpisodePack, index: number) {
    const step = pack.steps[index];
    if (episodeLayerIds === null) setPanel('episodes');
    setIsPlaying(false); setMode('explore'); setYear(step.year); setCameraCommand({ ...step.camera }); setCamera(step.camera); setCenter(step.camera.center); setZoom(step.camera.zoom);
    setLayers({ extents: true, nodes: true, routes: true, sources: true }); setEpisodeEntityIds(step.entityIds);
    setSelectedId(step.entityIds[0] ?? ''); setEpisodeLayerIds(step.layerIds); setEpisodeNotes(pack.annotations.filter((note) => step.annotationIds.includes(note.id)));
    const params = new URLSearchParams(location.search); params.set('episode', pack.id); params.set('episodeStep', step.id); history.replaceState(null, '', `?${params}`);
  }
  function exitEpisode() { setEpisodeEntityIds(null); setEpisodeLayerIds(null); setEpisodeNotes([]); setEpisodeAssets([]); const params = new URLSearchParams(location.search); params.delete('episode'); params.delete('episodeStep'); history.replaceState(null, '', `?${params}`); }
  function selectFeature(id: string) { setEpisodeStopToken((n) => n + 1); setSelectedId(id); setCameraCommand(undefined); setPanel('details'); }

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

  useEffect(() => {
    if (typeof window.matchMedia !== 'function') return;
    const query = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => { setReducedMotion(query.matches); if (query.matches) setIsPlaying(false); };
    update();
    query.addEventListener('change', update);
    return () => query.removeEventListener('change', update);
  }, []);

  // Research mode: hydrate view state from the URL on load (shareable views).
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const yearParam = params.get('y');
    const urlYear = yearParam === null ? NaN : Number(yearParam);
    if (Number.isInteger(urlYear) && urlYear >= YEAR_MIN && urlYear <= YEAR_MAX) {
      setYear(urlYear);
    }
    const urlSelected = params.get('sel');
    if (urlSelected) {
      setSelectedId(urlSelected);
      if (!params.has('lng') || !params.has('lat')) setCameraCommand(undefined);
    }
    const zoomParam = params.get('z'); const longitudeParam = params.get('lng'); const latitudeParam = params.get('lat');
    const urlZoom = zoomParam === null ? NaN : Number(zoomParam); const longitude = longitudeParam === null ? NaN : Number(longitudeParam); const latitude = latitudeParam === null ? NaN : Number(latitudeParam);
    if (Number.isFinite(urlZoom) && urlZoom >= 0 && urlZoom <= 20) setZoom(urlZoom);
    if (Number.isFinite(longitude) && Math.abs(longitude) <= 180 && Number.isFinite(latitude) && Math.abs(latitude) <= 85) {
      const numberParam = (key: string, fallback: number, min: number, max: number) => { const raw = params.get(key); const value = raw === null ? NaN : Number(raw); return Number.isFinite(value) ? Math.max(min, Math.min(max, value)) : fallback; };
      const view = { center: [longitude, latitude] as [number, number], zoom: numberParam('z', 1.8, 0, 20), bearing: numberParam('bearing', 0, -180, 180), pitch: numberParam('pitch', 0, 0, 60) };
      setCenter(view.center); setCamera(view); setCameraCommand(view);
    }
    const choices: Record<string, boolean> = {};
    params.get('boundaries')?.split(',').filter(Boolean).forEach((id) => { choices[id] = true; });
    params.get('hiddenBoundaries')?.split(',').filter(Boolean).forEach((id) => { choices[id] = false; });
    setBoundaryChoices(choices);
    setShowModernBorders(params.get('modernBorders') !== 'false');
    const encodedLayers = params.get('layers');
    if (encodedLayers !== null) setLayers((current) => ({ ...current, ...Object.fromEntries(encodedLayers.split(',').map((key) => [key, true])), ...Object.fromEntries(Object.keys(current).filter((key) => !encodedLayers.split(',').includes(key)).map((key) => [key, false])) }));
    setFilters({ confidence: (params.get('confidence')?.split(',').filter(Boolean) ?? []) as Confidence[], reviewStatus: (params.get('review')?.split(',').filter(Boolean) ?? []) as ReviewStatus[], layerTypes: params.get('types')?.split(',').filter(Boolean) ?? [] });
    const urlChapter = learningChapters.find((chapter) => chapter.id === params.get('chapter'));
    const urlStep = urlChapter?.steps.find((step) => step.id === params.get('step'));
    if (urlChapter && urlStep) {
      setMode('guided'); setChapterId(urlChapter.id); setStepId(urlStep.id);
      if (!params.has('y')) setYear(urlStep.year);
      if (!params.has('sel') && urlStep.selectedEntityId) setSelectedId(urlStep.selectedEntityId);
      if (!params.has('lng') || !params.has('lat')) { setCameraCommand(urlStep.camera); setCamera(urlStep.camera); setCenter(urlStep.camera.center); setZoom(urlStep.camera.zoom); }
      if (!params.has('layers')) setLayers({ extents: false, nodes: false, routes: false, sources: false, ...Object.fromEntries(urlStep.visibleLayers.map((key) => [key, true])) });
    }
    if (!params.has('z') && !urlStep && window.innerWidth < 768) { const mobileCamera: AtlasCamera = { center: [30, 25], zoom: 1.0, bearing: 0, pitch: 0 }; setCamera(mobileCamera); setCameraCommand(mobileCamera); setZoom(1.0); }
    setReady(true);
  }, []);

  // Research mode: keep the URL in sync with year + selection so any view is shareable.
  useEffect(() => {
    if (!ready) return;
    const params = new URLSearchParams(window.location.search);
    params.set('y', String(year));
    params.set('modernBorders', String(showModernBorders));
    if (selectedId) {
      params.set('sel', selectedId);
    }
    params.set('z', zoom.toFixed(2)); params.set('lng', center[0].toFixed(3)); params.set('lat', center[1].toFixed(3));
    params.set('bearing', (camera.bearing ?? 0).toFixed(1)); params.set('pitch', (camera.pitch ?? 0).toFixed(1));
    for (const [key, enabled] of [['boundaries', true], ['hiddenBoundaries', false]] as const) { const ids = Object.keys(boundaryChoices).filter((id) => boundaryChoices[id] === enabled); if (ids.length) params.set(key, ids.join(',')); else params.delete(key); }
    params.set('layers', Object.entries(layers).filter(([, active]) => active).map(([key]) => key).join(','));
    if (filters.confidence.length) params.set('confidence', filters.confidence.join(',')); else params.delete('confidence');
    if (filters.reviewStatus.length) params.set('review', filters.reviewStatus.join(',')); else params.delete('review');
    if (filters.layerTypes.length) params.set('types', filters.layerTypes.join(',')); else params.delete('types');
    if (mode === 'guided') { params.set('chapter', chapterId); params.set('step', stepId); } else { params.delete('chapter'); params.delete('step'); }
    const query = params.toString();
    window.history.replaceState(null, '', query ? `?${query}` : window.location.pathname);
  }, [ready, year, selectedId, zoom, center, camera, boundaryChoices, showModernBorders, layers, filters, mode, chapterId, stepId]);

  // Workstream D: timeline autoplay.
  useEffect(() => {
    if (!isPlaying || reducedMotion || backendStatus === 'loading' || backendStatus === 'unavailable') {
      return;
    }
    const intervalId = window.setInterval(() => {
      setYear((current) => {
        const proposed = current + PLAYBACK_STEP_YEARS;
        const crossedEvent = events.filter((event) => event.startYear > current && event.startYear <= proposed).sort((a, b) => a.startYear - b.startYear)[0];
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
  }, [isPlaying, playbackSpeed, pauseOnEvent, reducedMotion, events, backendStatus]);

  function stepTimeline(direction: -1 | 1, target: 'event' | 'era') {
    setEpisodeStopToken((n) => n + 1);
    setIsPlaying(false);
    const points = (target === 'event' ? events.flatMap((event) => [event.startYear, event.endYear]) : eras.flatMap((era) => [era.startYear, era.endYear])).filter((value, index, values) => values.indexOf(value) === index).sort((a, b) => a - b);
    const destination = direction > 0 ? points.find((point) => point > year) : [...points].reverse().find((point) => point < year);
    if (destination !== undefined) setYear(destination);
  }

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement || event.target instanceof HTMLSelectElement || event.target instanceof HTMLElement && (event.target.closest('button, a, [role=application], [contenteditable=true]'))) return;
      if (event.code === 'Space') { event.preventDefault(); togglePlay(); }
      if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') { event.preventDefault(); stepTimeline(event.key === 'ArrowLeft' ? -1 : 1, event.shiftKey ? 'era' : 'event'); }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  });

  function togglePlay() {
    if (episodeLayerIds !== null) setEpisodeStopToken((n) => n + 1);
    if (reducedMotion) return;
    setIsPlaying((current) => {
      // Restart from the beginning if we're paused at the end of the timeline.
      if (!current && year >= YEAR_MAX) {
        setYear(YEAR_MIN);
      }
      return !current;
    });
  }

  const activeWorld = useMemo(() => ({ ...baseWorld, layers: availableLayers(baseWorld.layers, sources) }), [baseWorld, sources]);
  const selectedLayers = useMemo(() => (episodeLayerIds === null ? visibleBoundaryLayers(activeWorld.layers, boundaryChoices) : activeWorld.layers.filter((layer) => episodeLayerIds.includes(layer.id))), [activeWorld.layers, boundaryChoices, episodeLayerIds]);
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
      layers: selectedLayers.filter((layer) => layers.extents && filteredWorld.civilizations.some((item) => item.id === layer.civilizationId)),
      civilizations: layers.extents ? filteredWorld.civilizations : [],
      nodes: layers.nodes ? filteredWorld.nodes.filter((node) => episodeEntityIds === null || episodeEntityIds.includes(node.id)) : [],
      routes: layers.routes ? filteredWorld.routes.filter((route) => episodeEntityIds === null || episodeEntityIds.includes(route.id)) : [],
    }),
    [filteredWorld, selectedLayers, layers.extents, layers.nodes, layers.routes, episodeEntityIds],
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

  function exportCurrentView() {
    const payload = {
      schemaVersion: 2,
      exportedAt: new Date().toISOString(),
      query: { year, selectedId, zoom, center, bearing: camera.bearing ?? 0, pitch: camera.pitch ?? 0, layers, filters, boundaryChoices },
      world: visibleWorld,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `civil-atlas-${year}-view.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  function applyLessonStep(nextChapterId: string, nextStepId: string) {
          setEpisodeStopToken((n) => n + 1);
          const chapter = learningChapters.find((item) => item.id === nextChapterId);
          const step = chapter?.steps.find((item) => item.id === nextStepId);
          if (!step) return;
          setIsPlaying(false); setCameraCommand({ ...step.camera }); setCamera(step.camera); setCenter(step.camera.center); setZoom(step.camera.zoom); setPanel(null);
          setChapterId(nextChapterId); setStepId(nextStepId); setYear(step.year);
          if (step.selectedEntityId) setSelectedId(step.selectedEntityId);
          setLayers({ extents: false, nodes: false, routes: false, sources: false, ...Object.fromEntries(step.visibleLayers.map((layer) => [layer, true])) });
  }

  return (
    <SiteShell
      title="Civil Atlas"
      subtitle="Main atlas interface"
    >
      <AtlasPage
        notesContent={<AnnotationNotebook year={year} notes={notebook.notes} onChange={notebook.setNotes} ready={notebook.ready} warning={notebook.warning} drawMode={drawMode === 'Rectangle' ? null : drawMode} points={drawPoints} onDraw={(mode) => { setDrawMode(mode); setDrawPoints([]); setPanel(null); }} onAddPoint={addDrawPoint} onCancel={cancelDrawing} />}
        researchContent={<ResearchWorkbench year={year} bounds={bounds} rectangle={rectangle} layers={activeWorld.layers} onDrawRectangle={() => { setRectangle(null); setDrawMode('Rectangle'); setDrawPoints([]); setPanel(null); }} />}
        episodesContent={<EpisodePlayer stopToken={episodeStopToken} coverageReady={backendStatus !== 'loading' && backendStatus !== 'unavailable' && (episodeLayerIds ?? []).every((id) => activeWorld.layers.some((layer) => layer.id === id))} missingLayers={(episodeLayerIds ?? []).filter((id) => !activeWorld.layers.some((layer) => layer.id === id))} onStep={applyEpisodeStep} onAssets={setEpisodeAssets} onExit={exitEpisode} reducedMotion={reducedMotion} />}
        statusContent={<LayerStatusPanel status={{ delivery: backendStatus === 'live' ? 'ready' : backendStatus, year, recordCount: activeWorld.civilizations.length + activeWorld.nodes.length + activeWorld.routes.length, layers: selectedLayers }} />}
        panel={panel}
        onPanelChange={setPanel}
        onRetry={reload}
        catalogFailed={catalogFailed}
        selectedLayerIds={selectedLayers.map((layer) => layer.id)}
        onBoundaryChange={(id, checked) => setBoundaryChoices((current) => ({ ...current, [id]: checked }))}
        chapters={learningChapters}
        chapterId={chapterId}
        mode={mode}
        stepId={stepId}
        onModeChange={(nextMode) => { setMode(nextMode); if (nextMode === 'guided') applyLessonStep(chapterId, stepId); }}
        onLessonStep={applyLessonStep}
        onExport={exportCurrentView}
        backendStatus={backendStatus}
        confidenceCounts={confidenceCounts}
        detailWorld={activeWorld}
        eras={eras}
        events={events}
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
              annotations={mapNotes}
              imageOverlays={imageOverlays}
              drawMode={drawMode}
              onDrawPoint={addDrawPoint}
              onFinishDraw={() => { if (drawMode === 'Rectangle') { cancelDrawing(); setPanel('research'); } else setPanel('notes'); }}
              onBoundsChange={(value) => { const [w, south, e, n] = value; const wrap = (x: number) => ((x + 180) % 360 + 360) % 360 - 180; setBounds(e - w >= 360 ? [-180, Math.max(-90, south), 180, Math.min(90, n)] : [wrap(w), Math.max(-90, south), wrap(e), Math.min(90, n)]); }}
              cameraCommand={cameraCommand}
              onCameraChange={(view) => { setCamera(view); setCenter(view.center); setZoom(view.zoom); }}
              reducedMotion={reducedMotion}
              cliopatriaVisible={visibleWorld.layers.some((layer) => isCliopatria(layer, sources))}
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
              showModernBorders={showModernBorders}
              showRoutes={layers.routes}
              onCivilizationSelect={selectFeature}
              onNodeSelect={selectFeature}
              onRouteSelect={selectFeature}
              onZoomChange={setZoom}
              onCenterChange={setCenter}
            />
          </Suspense>
        }
        onCivilizationSelect={selectFeature}
        onConfidenceToggle={toggleConfidence}
        onLayerTypeToggle={toggleLayerType}
        onResetFilters={() => setFilters(emptyFilterState)}
        onReviewStatusToggle={toggleReviewStatus}
        showModernBorders={showModernBorders}
        onToggleModernBorders={() => setShowModernBorders((value) => !value)}
        onToggleLayer={toggleLayer}
        onTogglePlay={togglePlay}
        playbackSpeed={playbackSpeed}
        pauseOnEvent={pauseOnEvent}
        reducedMotion={reducedMotion}
        onPlaybackSpeedChange={setPlaybackSpeed}
        onPauseOnEventChange={setPauseOnEvent}
        onStep={stepTimeline}
        onYearChange={(value) => { setEpisodeStopToken((n) => n + 1); setIsPlaying(false); setYear(value); }}
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
