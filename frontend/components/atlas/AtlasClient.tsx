'use client';

import { Suspense, lazy, useEffect, useMemo, useState } from 'react';
import { world117 } from '../../data/world117';
import {
  API_BASE_URL,
  DEFAULT_YEAR,
  HAS_REMOTE_API,
  filterWorldByYear,
  getFeatureById,
} from '../../lib/atlas';
import type { WorldPayload } from '../../types/atlas';
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

  const activeWorld = useMemo(() => filterWorldByYear(baseWorld, year), [baseWorld, year]);
  const visibleWorld = useMemo(
    () => ({
      ...activeWorld,
      civilizations: layers.extents ? activeWorld.civilizations : [],
      nodes: layers.nodes ? activeWorld.nodes : [],
      routes: layers.routes ? activeWorld.routes : [],
    }),
    [activeWorld, layers.extents, layers.nodes, layers.routes],
  );
  const selectedFeature = useMemo(
    () => getFeatureById(activeWorld, selectedId) ?? getFeatureById(baseWorld, selectedId),
    [activeWorld, baseWorld, selectedId],
  );
  const highlightedIds = useMemo(
    () =>
      layers.sources
        ? selectedFeature?.evidence.map((record) => record.id) ?? []
        : [],
    [layers.sources, selectedFeature],
  );

  function toggleLayer(layer: keyof LayerVisibility) {
    setLayers((current) => ({ ...current, [layer]: !current[layer] }));
  }

  return (
    <SiteShell
      title="Civil Atlas"
      subtitle="Main atlas interface"
    >
      <AtlasPage
        backendStatus={backendStatus}
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
        onToggleLayer={toggleLayer}
        onYearChange={setYear}
        selectedFeature={selectedFeature}
        selectedId={selectedId}
        world={activeWorld}
        year={year}
        zoom={zoom}
      />
    </SiteShell>
  );
}
