'use client';
import { useEffect, useRef, useState } from 'react';
import { AtlasMap } from '../map/AtlasMap';
import { useAtlasData } from '../atlas/hooks/useAtlasData';
import { LayerStatusPanel } from '../research/LayerStatusPanel';
import { PolityComparisonTable } from './PolityComparisonTable';
import { availableLayers, isCliopatria, visibleBoundaryLayers } from '../../lib/research';
import type { AtlasCamera, ComparisonState } from '../../types/atlas';

const initial: ComparisonState = { leftYear: 117, rightYear: 123, leftLayer: '', rightLayer: '', linked: true, camera: { center: [30, 30], zoom: 1.8, bearing: 0, pitch: 0 } };
function Pane({ side, year, layer, onYear, onLayer, command, onCamera, showModernBorders }: { side: string; year: number; layer: string; onYear: (year: number) => void; onLayer: (layer: string) => void; command: AtlasCamera; onCamera: (view: AtlasCamera) => void; showModernBorders: boolean }) {
  const data = useAtlasData(year, true);
  const [actualCamera, setActualCamera] = useState(command);
  const available = availableLayers(data.world.layers, data.sources);
  const selected = layer ? available.filter((item) => item.id === layer) : visibleBoundaryLayers(available, {});
  return <section className="comparison-pane" aria-label={`${side} comparison map`}>
    <div className="flex flex-wrap items-end gap-3 p-4"><label className="text-sm">{side} year<input className="research-input block" type="number" min={-600} max={1800} value={year} onChange={(e) => { const n = Number(e.target.value); if (Number.isInteger(n) && n >= -600 && n <= 1800) onYear(n); }} /></label>
      <label className="min-w-0 flex-1 text-sm">Boundary interpretation<select className="research-input block w-full" value={layer} onChange={(e) => onLayer(e.target.value)}><option value="">Primary interpretations</option>{available.map((item) => <option key={item.id} value={item.id}>{item.interpretationLabel || item.name}</option>)}{layer && !available.some((item) => item.id === layer) && <option value={layer}>Unavailable at this date</option>}</select></label>
    </div>
    <div className="comparison-map relative"><AtlasMap showModernBorders={showModernBorders} initialCenter={command.center} initialZoom={command.zoom} cameraCommand={command} onCameraChange={(camera, origin) => { setActualCamera(camera); if (origin !== 'command') onCamera(camera); }} civilizations={data.world.civilizations} civilizationLayers={selected} nodes={data.world.nodes} routes={data.world.routes} evidenceIds={[]} showEvidence={false} showExtents showNodes showRoutes cliopatriaVisible={selected.some((item) => isCliopatria(item, data.sources))} onCivilizationSelect={() => {}} onNodeSelect={() => {}} onRouteSelect={() => {}} onCenterChange={() => {}} onZoomChange={() => {}} />{!selected.length && data.status !== 'loading' && <div className="comparison-missing" role="status">No boundary coverage for this date and interpretation.</div>}</div>
    <output className="mx-4 block text-xs text-slate-300" aria-label={`${side} camera`}>Longitude {actualCamera.center[0].toFixed(2)} · latitude {actualCamera.center[1].toFixed(2)} · zoom {actualCamera.zoom.toFixed(2)}</output>
    <LayerStatusPanel status={{ delivery: data.status === 'live' ? 'ready' : data.status, year, recordCount: data.world.civilizations.length, layers: selected }} compact />
    {data.status === 'unavailable' && <button className="atlas-tool m-3" onClick={data.reload} type="button">Retry {side.toLowerCase()} data</button>}
  </section>;
}
export function ComparisonWorkspace() {
  const [view, setView] = useState(initial);
  const [showModernBorders, setShowModernBorders] = useState(true);
  const [ready, setReady] = useState(false);
  const [tab, setTab] = useState('maps');
  const [leftCamera, setLeftCamera] = useState(initial.camera), [rightCamera, setRightCamera] = useState(initial.camera);
  const settled = useRef(initial.camera);
  useEffect(() => {
    const p = new URLSearchParams(location.search);
    setShowModernBorders(p.get('modernBorders') !== 'false');
    const year = (key: string, fallback: number) => { const n = p.has(key) ? Number(p.get(key)) : NaN; return Number.isInteger(n) && n >= -600 && n <= 1800 ? n : fallback; };
    const camera = { ...initial.camera };
    if (p.has('lng') && p.has('lat')) { const lng = Number(p.get('lng')), lat = Number(p.get('lat')); if (Number.isFinite(lng) && Math.abs(lng) <= 180 && Number.isFinite(lat) && Math.abs(lat) <= 85) camera.center = [lng, lat]; }
    for (const key of ['zoom', 'bearing', 'pitch'] as const) { const raw = p.get(key), n = Number(raw); if (raw !== null && Number.isFinite(n)) camera[key] = Math.max(key === 'bearing' ? -180 : 0, Math.min(key === 'zoom' ? 20 : key === 'pitch' ? 60 : 180, n)); }
    setView({ leftYear: year('leftYear', 117), rightYear: year('rightYear', 123), leftLayer: p.get('leftLayer') || '', rightLayer: p.get('rightLayer') || '', linked: p.get('linked') !== 'false', camera });
    setLeftCamera(camera); setRightCamera(camera); settled.current = camera; if (p.get('tab') === 'table') setTab('table'); setReady(true);
  }, []);
  useEffect(() => { if (!ready) return; const p = new URLSearchParams({ leftYear: String(view.leftYear), rightYear: String(view.rightYear), leftLayer: view.leftLayer, rightLayer: view.rightLayer, linked: String(view.linked), modernBorders: String(showModernBorders), tab, lng: String(view.camera.center[0]), lat: String(view.camera.center[1]), zoom: String(view.camera.zoom), bearing: String(view.camera.bearing ?? 0), pitch: String(view.camera.pitch ?? 0) }); history.replaceState(null, '', `?${p}`); }, [view, showModernBorders, tab, ready]);
  function cameraChanged(side: 'left' | 'right', camera: AtlasCamera) {
    if (JSON.stringify(settled.current) === JSON.stringify(camera)) return;
    settled.current = camera; setView((current) => ({ ...current, camera }));
    (side === 'left' ? setLeftCamera : setRightCamera)(camera);
    if (view.linked) (side === 'left' ? setRightCamera : setLeftCamera)(camera);
  }
  return <main><header className="atlas-panel rounded-2xl p-5"><p className="atlas-kicker">Compare historical readings</p><h1 className="mt-2 text-3xl">Two views. Their evidence.</h1><p className="mt-3 text-sm text-slate-300">Compare dates or source interpretations. Missing coverage stays visible; the basemap provides modern geographic context.</p><div className="mt-4 flex flex-wrap gap-3"><button className="atlas-tool" type="button" aria-pressed={tab === 'maps'} onClick={() => setTab('maps')}>Linked maps</button><button className="atlas-tool" type="button" aria-pressed={tab === 'table'} onClick={() => setTab('table')}>Polity table</button><label className="text-sm"><input className="mr-2" type="checkbox" checked={view.linked} onChange={(e) => { const linked = e.target.checked; setView((v) => ({ ...v, linked })); if (linked) { setLeftCamera(settled.current); setRightCamera(settled.current); } }} />Synchronize cameras</label><label className="text-sm"><input className="mr-2" type="checkbox" checked={showModernBorders} onChange={(event) => setShowModernBorders(event.target.checked)} />Present-day borders</label></div></header>
    {tab === 'table' ? <PolityComparisonTable /> : ready && <div className="comparison-grid mt-4"><Pane showModernBorders={showModernBorders} side="Left" year={view.leftYear} layer={view.leftLayer} onYear={(leftYear) => setView((v) => ({ ...v, leftYear }))} onLayer={(leftLayer) => setView((v) => ({ ...v, leftLayer }))} command={leftCamera} onCamera={(c) => cameraChanged('left', c)} /><Pane showModernBorders={showModernBorders} side="Right" year={view.rightYear} layer={view.rightLayer} onYear={(rightYear) => setView((v) => ({ ...v, rightYear }))} onLayer={(rightLayer) => setView((v) => ({ ...v, rightLayer }))} command={rightCamera} onCamera={(c) => cameraChanged('right', c)} /></div>}
  </main>;
}
