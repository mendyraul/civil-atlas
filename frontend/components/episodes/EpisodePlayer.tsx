'use client';
import { useEffect, useRef, useState } from 'react';
import { API_BASE_URL, DEMO_MODE, HAS_REMOTE_API, normalizeApiPayload } from '../../lib/atlas';
import { downloadJson } from '../../lib/annotations';
import { loadAsset, parseEpisode, validateEpisode, type EpisodeBundle, type LoadedAsset } from '../../lib/episodes';
import { connectedWorldDemo } from '../../data/episodes';
import type { EpisodePack } from '../../types/atlas';
export function EpisodePlayer({ onStep, onAssets, onExit, reducedMotion, coverageReady = true, missingLayers = [], stopToken = 0 }: { onStep: (pack: EpisodePack, index: number) => void; onAssets: (assets: LoadedAsset[]) => void; onExit: () => void; reducedMotion: boolean; coverageReady?: boolean; missingLayers?: string[]; stopToken?: number }) {
  const [origin, setOrigin] = useState<'published' | 'local' | 'demo'>('local');
  const [packs, setPacks] = useState<EpisodePack[]>([]), [bundle, setBundle] = useState<EpisodeBundle | null>(null), [preview, setPreview] = useState<EpisodeBundle | null>(null), [index, setIndex] = useState(0), [playing, setPlaying] = useState(false), [error, setError] = useState(''), [assetError, setAssetError] = useState(''), [assets, setAssets] = useState<LoadedAsset[]>([]), [assetsReady, setAssetsReady] = useState(false);
  const previousStop = useRef(stopToken);
  const callbacks = useRef({ onStep, onAssets, onExit }); callbacks.current = { onStep, onAssets, onExit };
  useEffect(() => { const controller = new AbortController(); if (HAS_REMOTE_API) fetch(`${API_BASE_URL}/api/v1/episodes`, { signal: controller.signal }).then(async (r) => { if (!r.ok) throw Error('Published episodes are unavailable.'); const values = normalizeApiPayload<unknown[]>(await r.json()); if (controller.signal.aborted) return; const available = values.map(validateEpisode); setPacks(available);
      const params = new URLSearchParams(location.search); const target = available.find((p) => p.id === params.get('episode'));
      if (target) { open({ schemaVersion: 1, pack: target }, 'published'); const index = target.steps.findIndex((s) => s.id === params.get('episodeStep')); if (index >= 0) setIndex(index); } else if (params.get('episode') && !(DEMO_MODE && params.get('episode') === connectedWorldDemo.id)) setError('Episode is not publicly available. Local files must be imported again.'); }).catch((e) => { if (!controller.signal.aborted) setError(e.message); }); return () => controller.abort(); }, []);
  useEffect(() => { const params = new URLSearchParams(location.search); if (DEMO_MODE && params.get('episode') === connectedWorldDemo.id) { open({ schemaVersion: 1, pack: connectedWorldDemo }, 'demo'); const index = connectedWorldDemo.steps.findIndex((s) => s.id === params.get('episodeStep')); if (index >= 0) setIndex(index); } }, []);
  useEffect(() => { if (previousStop.current !== stopToken) { previousStop.current = stopToken; setPlaying(false); setBundle(null); callbacks.current.onExit(); } }, [stopToken]);
  const pack = bundle?.pack, step = pack?.steps[index];
  useEffect(() => { if (pack) callbacks.current.onStep(pack, index); }, [pack, index]);
  useEffect(() => {
    const controller = new AbortController(); const owned: LoadedAsset[] = []; let live = true;
    setAssets([]); callbacks.current.onAssets([]); setAssetError(''); setAssetsReady(false);
    if (!pack || !step) return () => controller.abort();
    async function load() {
      try {
        for (const asset of pack!.assets.filter((a) => step!.assetIds.includes(a.id))) { const loaded = await loadAsset(asset, bundle?.files, controller.signal); if (!live) { URL.revokeObjectURL(loaded.url); return; } owned.push(loaded); }
        if (live) { setAssets([...owned]); callbacks.current.onAssets([...owned]); setAssetsReady(true); }
      } catch { if (live) { owned.forEach((a) => URL.revokeObjectURL(a.url)); setAssetError('Episode assets could not be loaded or verified. Stop, change step, or retry the episode.'); setPlaying(false); } }
    }
    void load();
    return () => { live = false; controller.abort(); owned.forEach((a) => URL.revokeObjectURL(a.url)); };
  }, [pack, step, bundle]);
  useEffect(() => { if (!playing || reducedMotion || !step || !assetsReady || !coverageReady) return; const timer = window.setTimeout(() => { if (index >= pack!.steps.length - 1) setPlaying(false); else setIndex(index + 1); }, step.holdSeconds * 1000); return () => clearTimeout(timer); }, [playing, reducedMotion, step, assetsReady, index, pack, coverageReady]);
  useEffect(() => { if (reducedMotion) setPlaying(false); }, [reducedMotion]);
  function open(next: EpisodeBundle, source: 'published' | 'local' | 'demo' = 'local') { setOrigin(source); setPlaying(false); setIndex(0); setBundle(next); setPreview(null); setError(''); }
  return <section className="research-card" aria-label="Historical episodes"><h2 className="text-xl">Historical episodes</h2><p className="mt-2 text-sm text-slate-300">Curated journeys carry their dates, geography, citations, and asset credits together.</p>
    {packs.map((p) => <button className="atlas-tool mt-3 block" type="button" key={p.id} onClick={() => open({ schemaVersion: 1, pack: p }, 'published')}>{p.title}</button>)}
    {DEMO_MODE && <button className="atlas-tool mt-3" type="button" onClick={() => open({ schemaVersion: 1, pack: connectedWorldDemo }, 'demo')}>Preview connected-world demo</button>}
    {!packs.length && <p className="mt-3 text-sm">No reviewed episodes are currently available from the public API.</p>}
    <label className="mt-4 block text-sm">Import an episode or bundle<input className="mt-2 block w-full" type="file" accept="application/json,.json" onChange={async (e) => { try { const file = e.target.files?.[0]; if (file) { if (file.size > 32 * 1024 * 1024) throw Error('Episode exceeds 32 MiB.'); setPreview(parseEpisode(await file.text())); setError(''); } } catch (error) { setError((error as Error).message); } e.target.value = ''; }} /></label>
    {preview && <div className="mt-3 border border-white/20 p-3"><h3>Import preview: {preview.pack.title}</h3><p className="mt-2 text-sm">{preview.pack.steps.length} steps · {preview.pack.annotations.length} annotations · {preview.pack.assets.length} assets. Local file content is not published or independently verified.</p><p className="mt-2 text-xs">{preview.pack.attribution}</p>{preview.pack.assets.map((a) => <p className="mt-1 text-xs" key={a.id}>{a.attribution} · {a.license}</p>)}<button className="atlas-tool mt-3" type="button" onClick={() => open(preview)}>Open local episode</button><button className="atlas-tool ml-2" type="button" onClick={() => setPreview(null)}>Cancel import</button></div>}
    {error && <p role="alert" className="mt-3 text-amber-100">{error}</p>}
    {pack && step && <div className="mt-5"><p className="text-xs text-amber-100">{origin !== 'published' ? 'Local / demonstration content · unreviewed' : 'Published episode'} · {pack.datasetVersion}</p><h3 className="mt-2 text-lg">{pack.title}</h3><p className="mt-2 text-sm">Step {index + 1}/{pack.steps.length} · {step.year < 0 ? `${-step.year} BCE` : `${step.year} CE`}</p><h4 className="mt-3 font-semibold">{step.title}</h4><p className="mt-2 text-sm leading-6">{step.narrative}</p>{missingLayers.length > 0 && <p className="mt-3 text-xs text-amber-100" role="status">Waiting for the step’s published boundary coverage. Unavailable layers are not substituted.</p>}{!step.layerIds.length && <p className="mt-3 text-xs text-amber-100">This step has no reviewed territorial geometry. No placeholder territory is substituted.</p>}<div className="mt-4 flex flex-wrap gap-2"><button className="atlas-tool" type="button" disabled={!index} onClick={() => { setPlaying(false); setIndex(index - 1); }}>Previous step</button><button className="atlas-tool" disabled={reducedMotion || Boolean(assetError) || !coverageReady} type="button" onClick={() => setPlaying(!playing)}>{playing ? 'Pause episode' : 'Play episode'}</button><button className="atlas-tool" type="button" disabled={index >= pack.steps.length - 1} onClick={() => { setPlaying(false); setIndex(index + 1); }}>Next step</button><button className="atlas-tool" type="button" onClick={() => { setPlaying(false); setBundle(null); callbacks.current.onExit(); }}>Stop episode</button></div>
      <p className="mt-3 text-xs">{pack.attribution} · {pack.license}</p><div className="mt-3">{step.sourceRecordIds.map((id) => <a className="mb-2 block text-xs text-cyan-200 underline" href={`/sources/${encodeURIComponent(id)}`} key={id}>Source record: {id}</a>)}</div>
      {assetError && <p role="alert" className="mt-3 text-amber-100">{assetError}</p>}
      {assets.map(({ asset, url }) => <div className="mt-3" key={asset.id}>{asset.kind === 'audio' ? <audio controls src={url} aria-label={asset.attribution} /> : asset.kind === 'video' ? <video controls src={url} aria-label={asset.attribution} className="w-full" /> : <p className="text-xs">Historical map overlay displayed at its supplied bounds.</p>}<p className="mt-2 text-xs">{asset.attribution} · {asset.license}{asset.coordinates ? ` · ${asset.coordinates.join(', ')}` : ''}</p></div>)}
      <button className="atlas-tool mt-3" type="button" onClick={() => downloadJson(`${pack.id}.episode.json`, bundle)}>Export episode{bundle?.files ? ' bundle' : ''}</button>
    </div>}
  </section>;
}
