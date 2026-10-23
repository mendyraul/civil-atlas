'use client';

import { useEffect, useRef, useState } from 'react';
import { API_BASE_URL, DEMO_MODE, HAS_REMOTE_API, normalizeApiPayload } from '../../../lib/atlas';
import { world117 } from '../../../data/demoWorld117';
import { loadDemoWorld, previewSources } from '../../../lib/demoHistory';
import type { Era, HistoricalEvent, SourceRecord, WorldPayload } from '../../../types/atlas';

export function emptyWorld(year: number): WorldPayload {
  return { year, civilizations: [], nodes: [], routes: [], layers: [], relationships: [], eras: [], events: [] };
}

export function useAtlasData(year: number, ready: boolean) {
  const cache = useRef(new Map<number, WorldPayload>());
  const [loaded, setLoaded] = useState<WorldPayload | null>(DEMO_MODE ? world117 : null);
  const [failedYear, setFailedYear] = useState<number | null>(null);
  const [retry, setRetry] = useState(0);
  const [catalog, setCatalog] = useState<{ eras: Era[]; events: HistoricalEvent[]; sources: SourceRecord[] }>({ eras: [], events: [], sources: [] });
  const [catalogReady, setCatalogReady] = useState(false);
  const [catalogFailed, setCatalogFailed] = useState(false);

  useEffect(() => {
    if (DEMO_MODE || !HAS_REMOTE_API || !ready) return;
    const controller = new AbortController();
    async function loadCatalog() {
      try {
        const [eras, events, sources] = await Promise.all(['eras', 'events', 'sources'].map(async (path) => {
          const response = await fetch(`${API_BASE_URL}/api/v1/${path}`, { signal: controller.signal, cache: 'no-store' });
          if (!response.ok) throw new Error('Catalog unavailable');
          return normalizeApiPayload(await response.json());
        }));
        if (!controller.signal.aborted) { setCatalog({ eras: eras as Era[], events: events as HistoricalEvent[], sources: sources as SourceRecord[] }); setCatalogReady(true); setCatalogFailed(false); }
      } catch { if (!controller.signal.aborted) setCatalogFailed(true); }
    }
    void loadCatalog();
    return () => controller.abort();
  }, [ready, retry]);

  useEffect(() => {
    if ((!DEMO_MODE && !HAS_REMOTE_API) || !ready) return;
    if (cache.current.has(year)) { setLoaded(cache.current.get(year)!); return; }
    const controller = new AbortController();
    const timeout = window.setTimeout(async () => {
      try {
        const world = DEMO_MODE ? await loadDemoWorld(year) : await (async () => {
          const response = await fetch(`${API_BASE_URL}/api/v1/world/${year}`, { signal: controller.signal, cache: 'no-store' });
          if (!response.ok) throw new Error('World unavailable');
          return normalizeApiPayload<WorldPayload>(await response.json());
        })();
        if (world.year !== year) throw new Error('Unexpected world year');
        if (!controller.signal.aborted) {
          cache.current.set(year, world);
          if (cache.current.size > 80) cache.current.delete(cache.current.keys().next().value!);
          setLoaded(world); setFailedYear(null);
        }
      } catch { if (!controller.signal.aborted) setFailedYear(year); }
    }, 120);
    return () => { window.clearTimeout(timeout); controller.abort(); };
  }, [year, ready, retry]);

  const world = (DEMO_MODE || catalogReady) && loaded?.year === year ? loaded : emptyWorld(year);
  const status: 'demo' | 'unavailable' | 'live' | 'loading' = DEMO_MODE ? failedYear === year ? 'unavailable' : loaded?.year === year ? 'demo' : 'loading' : !HAS_REMOTE_API || failedYear === year || catalogFailed ? 'unavailable' : catalogReady && loaded?.year === year ? 'live' : 'loading';
  return {
    world, status, catalogFailed,
    eras: DEMO_MODE ? world117.eras : catalog.eras,
    events: DEMO_MODE ? world117.events : catalog.events,
    sources: DEMO_MODE ? previewSources : catalog.sources,
    reload: () => { cache.current.delete(year); setFailedYear(null); setLoaded(null); setRetry((value) => value + 1); },
  };
}
