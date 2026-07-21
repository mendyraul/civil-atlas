'use client';

import { Suspense, lazy, useEffect, useMemo, useState } from 'react';
import { world117 } from '../../data/world117';
import { StatusBadge } from '../badges/StatusBadge';
import { FeaturePanel } from '../panels/FeaturePanel';
import { TimelineControl } from '../timeline/TimelineControl';
import { API_BASE_URL, DEFAULT_YEAR, NODE_VISIBILITY_ZOOM, featureBadgeTone, filterWorldByYear, formatYear, getFeatureById } from '../../lib/atlas';
import type { WorldPayload } from '../../types/atlas';
import { SiteShell } from './SiteShell';

const LazyAtlasMap = lazy(async () => {
  const module = await import('../map/AtlasMap');
  return { default: module.AtlasMap };
});

export function AtlasClient() {
  const [baseWorld, setBaseWorld] = useState<WorldPayload>(world117);
  const [year, setYear] = useState(DEFAULT_YEAR);
  const [selectedId, setSelectedId] = useState<string>('roman-empire');
  const [zoom, setZoom] = useState(2.1);
  const [backendStatus, setBackendStatus] = useState<'seed' | 'live'>('seed');

  useEffect(() => {
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
  const selectedFeature = useMemo(
    () => getFeatureById(activeWorld, selectedId) ?? getFeatureById(baseWorld, selectedId),
    [activeWorld, baseWorld, selectedId],
  );

  return (
    <SiteShell
      title="World at 117 CE"
      subtitle="A historical operations dashboard for time-aware civilizations, routes, places, and evidence. Boundaries stay visibly provisional unless explicitly reviewed."
    >
      <section className="mb-5 grid grid-cols-1 gap-4 md:grid-cols-4">
        <div className="atlas-panel rounded-[24px] px-5 py-4">
          <span className="block text-xs uppercase tracking-[0.18em] text-[--muted]">Current year</span>
          <strong className="mt-2 block text-3xl">{formatYear(year)}</strong>
        </div>
        <div className="atlas-panel rounded-[24px] px-5 py-4">
          <span className="block text-xs uppercase tracking-[0.18em] text-[--muted]">Active civilizations</span>
          <strong className="mt-2 block text-3xl">{activeWorld.civilizations.length}</strong>
        </div>
        <div className="atlas-panel rounded-[24px] px-5 py-4">
          <span className="block text-xs uppercase tracking-[0.18em] text-[--muted]">Visible routes</span>
          <strong className="mt-2 block text-3xl">{activeWorld.routes.length}</strong>
        </div>
        <div className="atlas-panel rounded-[24px] px-5 py-4">
          <span className="block text-xs uppercase tracking-[0.18em] text-[--muted]">Data channel</span>
          <strong className="mt-2 block text-xl">
            {backendStatus === 'live' ? 'FastAPI live' : 'Seed fallback'}
          </strong>
        </div>
      </section>

      <main className="grid grid-cols-1 gap-5 xl:grid-cols-[320px_minmax(0,1fr)_360px]">
        <section className="flex flex-col gap-4">
          <TimelineControl year={year} onYearChange={setYear} />

          <div className="atlas-panel rounded-[24px] p-5">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold">Active polities</h2>
              <span className="text-sm text-[--muted]">{activeWorld.routes.length} routes</span>
            </div>
            <ul className="mt-4 flex flex-wrap gap-2">
              {activeWorld.civilizations.map((civilization) => (
                <li key={civilization.id}>
                  <button
                    className={`rounded-full border px-3 py-2 text-sm transition ${
                      selectedId === civilization.id
                        ? 'border-slate-900 bg-slate-900 text-amber-50'
                        : 'border-slate-300 bg-white/80 text-slate-800'
                    }`}
                    onClick={() => setSelectedId(civilization.id)}
                    type="button"
                  >
                    <span
                      className="mr-2 inline-block h-2.5 w-2.5 rounded-full"
                      style={{ backgroundColor: civilization.color }}
                    />
                    {civilization.displayName}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div className="atlas-panel rounded-[24px] p-5">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold">Uncertainty legend</h2>
              <span className="text-sm text-[--muted]">MVP signal</span>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {['Approximate', 'Source-reported', 'Placeholder geometry', 'Needs review'].map((badge) => (
                <StatusBadge label={badge} tone={featureBadgeTone(badge)} key={badge} />
              ))}
            </div>
          </div>

          <div className="atlas-panel rounded-[24px] p-5">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold">Zoom behavior</h2>
              <span className="text-sm text-[--muted]">{zoom.toFixed(1)}x</span>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-700">
              Extent layers and routes stay visible at world view. Place nodes
              appear once the map crosses roughly {NODE_VISIBILITY_ZOOM.toFixed(1)} zoom.
            </p>
            <p className="mt-3 text-sm text-[--muted]">
              Visible nodes now: {zoom >= NODE_VISIBILITY_ZOOM ? activeWorld.nodes.length : 0}
            </p>
          </div>
        </section>

        <section className="overflow-hidden rounded-[28px] border border-slate-300/70 bg-[#d9e6e8] shadow-[0_24px_60px_rgba(61,45,18,0.12)]">
          <Suspense
            fallback={
              <div className="grid h-[68vh] min-h-[560px] place-items-center text-lg tracking-[0.04em] text-slate-700">
                Loading atlas...
              </div>
            }
          >
            <LazyAtlasMap
              civilizations={activeWorld.civilizations}
              nodes={activeWorld.nodes}
              routes={activeWorld.routes}
              selectedId={selectedId}
              onCivilizationSelect={setSelectedId}
              onNodeSelect={setSelectedId}
              onRouteSelect={setSelectedId}
              onZoomChange={setZoom}
            />
          </Suspense>
        </section>

        <FeaturePanel feature={selectedFeature} world={baseWorld} />
      </main>
    </SiteShell>
  );
}
