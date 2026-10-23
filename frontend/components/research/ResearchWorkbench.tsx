'use client';
import { useEffect, useRef, useState } from 'react';
import { API_BASE_URL, HAS_REMOTE_API, normalizeApiPayload } from '../../lib/atlas';
import type { CivilizationLayer, ResearchArea, ResearchQuery, ResearchResult } from '../../types/atlas';
export function ResearchWorkbench({ year, bounds, rectangle, onDrawRectangle, layers }: { year: number; bounds: [number, number, number, number]; rectangle: [number, number, number, number] | null; onDrawRectangle: () => void; layers: CivilizationLayer[] }) {
  const activeRequest = useRef<AbortController | null>(null);
  const [areaType, setAreaType] = useState('viewport'), [operation, setOperation] = useState<'entities_in_area' | 'events_in_area'>('entities_in_area'), [layerId, setLayerId] = useState('');
  const [longitude, setLongitude] = useState(30), [latitude, setLatitude] = useState(35), [radius, setRadius] = useState(250);
  const [result, setResult] = useState<ResearchResult | null>(null), [busy, setBusy] = useState(false), [error, setError] = useState('');
  useEffect(() => { activeRequest.current?.abort(); setResult(null); setBusy(false); return () => activeRequest.current?.abort(); }, [year]);
  async function run(page = 1) {
    activeRequest.current?.abort(); const controller = new AbortController(); activeRequest.current = controller;
    setBusy(true); setError(''); setResult(null);
    try {
      if (!HAS_REMOTE_API) throw Error('Configure the public API to query the historical database.');
      let area: ResearchArea = { bbox: bounds };
      if (areaType === 'rectangle') { if (!rectangle) throw Error('Draw a search rectangle first.'); area = { bbox: rectangle }; }
      if (areaType === 'radius') { if (!Number.isFinite(longitude) || !Number.isFinite(latitude) || !Number.isFinite(radius)) throw Error('Enter valid coordinates and radius.'); area = { center: [longitude, latitude], radiusKm: radius }; }
      if (areaType === 'boundary') { if (!layerId) throw Error('Select a reviewed boundary.'); area = { layerId }; }
      const query: ResearchQuery = { operation, year, area, page, pageSize: 20 };
      const response = await fetch(`${API_BASE_URL}/api/v1/research/query`, { signal: controller.signal, method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(query) });
      if (!response.ok) throw Error(response.status === 422 ? 'Check the area, dates, and availability of the selected boundary.' : 'Historical research is unavailable. Retry when the API is reachable.');
      const result = normalizeApiPayload<ResearchResult>(await response.json()); if (!controller.signal.aborted) setResult(result);
    } catch (error) { if (!controller.signal.aborted) setError((error as Error).message); } finally { if (activeRequest.current === controller) setBusy(false); }
  }
  return <section className="research-card" aria-label="Geographic research"><h2 className="text-xl">Research this geography</h2><p className="mt-2 text-sm text-slate-300">Search published records at the atlas year. Results describe the database’s coverage.</p>
    <label className="mt-4 block">Find<select aria-label="Find" className="research-input block w-full" value={operation} onChange={(e) => setOperation(e.target.value as typeof operation)}><option value="entities_in_area">Territories, places, and routes</option><option value="events_in_area">Events recorded in this year</option></select></label>
    <label className="mt-3 block">Area<select aria-label="Area" className="research-input block w-full" value={areaType} onChange={(e) => setAreaType(e.target.value)}><option value="viewport">Current map bounds</option><option value="rectangle">Drawn rectangle</option><option value="radius">Point and radius</option><option value="boundary">Historical boundary</option></select></label>
    {areaType === 'rectangle' && <div className="mt-3"><button className="atlas-tool" type="button" onClick={onDrawRectangle}>Draw search rectangle</button><p className="mt-2 text-xs">{rectangle ? `Selected bounds: ${rectangle.map((n) => n.toFixed(2)).join(', ')}` : 'Click two corners on the globe.'}</p></div>}
    {areaType === 'radius' && <div className="mt-3 grid gap-2">{([['Longitude', longitude, setLongitude, -180, 180], ['Latitude', latitude, setLatitude, -90, 90], ['Radius (km)', radius, setRadius, 0.1, 2000]] as const).map(([label, value, setter, min, max]) => <label key={label}>{label}<input className="research-input block w-full" type="number" min={min} max={max} value={value} onChange={(e) => setter(Number(e.target.value))} /></label>)}</div>}
    {areaType === 'boundary' && <label className="mt-3 block">Reviewed boundary<select className="research-input block w-full" value={layerId} onChange={(e) => setLayerId(e.target.value)}><option value="">Choose a boundary</option>{layers.filter((l) => l.reviewStatus === 'reviewed' && !l.isPlaceholder && !l.geometryPlaceholder).map((l) => <option key={l.id} value={l.id}>{l.interpretationLabel || l.name}</option>)}</select></label>}
    <button className="atlas-tool mt-4" type="button" disabled={busy} onClick={() => run()}>{busy ? 'Searching…' : `Search ${year < 0 ? `${-year} BCE` : `${year} CE`}`}</button>
    {error && <p role="alert" className="mt-3 text-amber-100">{error}</p>}
    {result && <div className="mt-4" aria-live="polite"><h3>{result.summary}</h3><p className="mt-2 text-xs text-slate-300">Dataset {result.dataVersion} · {result.unlocatedCount} records have no usable geography.</p>{result.limitations.map((limit) => <p className="mt-2 text-xs text-amber-100" key={limit}>{limit}</p>)}<ul className="mt-3 space-y-3">{result.items.map((item, index) => <li className="border-t border-white/10 pt-2" key={String(item.record?.id ?? index)}><a className="text-cyan-200 underline" href={item.url}>{String(item.record?.label || item.record?.name || item.record?.title || item.record?.id)}</a><p className="mt-1 text-xs">{item.kind} · {String(item.record?.confidence)} confidence · {String(item.record?.reviewStatus).replace('_', ' ')}</p>{item.sources?.map((source) => <a className="mt-1 block text-xs text-cyan-100 underline" key={source.id} href={`/sources/${encodeURIComponent(source.id)}`}>{source.citation}</a>)}</li>)}</ul><div className="mt-3 flex gap-2"><button className="atlas-tool" disabled={result.page <= 1 || busy} type="button" onClick={() => run(result.page - 1)}>Previous results</button><button className="atlas-tool" disabled={result.page * result.pageSize >= result.total || busy} type="button" onClick={() => run(result.page + 1)}>Next results</button></div></div>}
  </section>;
}
