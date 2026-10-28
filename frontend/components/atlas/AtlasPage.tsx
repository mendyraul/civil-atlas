'use client';

import { useEffect, useRef } from 'react';
import { ActiveCivilizationsPanel } from './ActiveCivilizationsPanel';
import { AtlasFilters, type LayerTypeOption } from './AtlasFilters';
import { LayerControls } from './LayerControls';
import { DetailPanel } from './DetailPanel';
import { TimelineControl } from '../timeline/TimelineControl';
import { formatYear } from '../../lib/atlas';
import { boundaryGroup } from '../../lib/research';
import type { AtlasFeature, Confidence, Era, HistoricalEvent, LearningChapter, ReviewStatus, WorldPayload } from '../../types/atlas';

type LayerVisibility = {
  extents: boolean;
  nodes: boolean;
  routes: boolean;
  sources: boolean;
};

type AtlasPageProps = {
  panel: 'layers' | 'details' | 'notes' | 'research' | 'episodes' | 'status' | null;
  onPanelChange: (panel: 'layers' | 'details' | 'notes' | 'research' | 'episodes' | 'status' | null) => void;
  onRetry: () => void;
  catalogFailed: boolean;
  selectedLayerIds: string[];
  onBoundaryChange: (id: string, checked: boolean) => void;
  notesContent?: React.ReactNode;
  researchContent?: React.ReactNode;
  episodesContent?: React.ReactNode;
  statusContent?: React.ReactNode;
  year: number;
  zoom: number;
  backendStatus: 'live' | 'demo' | 'loading' | 'stale' | 'unavailable';
  confidenceCounts: Record<Confidence, number>;
  detailWorld: WorldPayload;
  eras: Era[];
  events: HistoricalEvent[];
  filterCount: number;
  isPlaying: boolean;
  playbackSpeed: number;
  pauseOnEvent: boolean;
  reducedMotion: boolean;
  chapters: LearningChapter[];
  chapterId: string;
  stepId: string;
  mode: 'explore' | 'guided';
  isSelectedFeatureFilteredOut: boolean;
  layerTypeOptions: LayerTypeOption[];
  reviewCounts: Record<ReviewStatus, number>;
  selectedId?: string;
  selectedConfidence: Confidence[];
  selectedFeature?: AtlasFeature;
  selectedLayerTypes: string[];
  selectedReviewStatus: ReviewStatus[];
  world: WorldPayload;
  layers: LayerVisibility;
  map: React.ReactNode;
  onConfidenceToggle: (confidence: Confidence) => void;
  onYearChange: (year: number) => void;
  onCivilizationSelect: (id: string) => void;
  onLayerTypeToggle: (value: string) => void;
  onResetFilters: () => void;
  onReviewStatusToggle: (status: ReviewStatus) => void;
  showModernBorders: boolean;
  onToggleModernBorders: () => void;
  onToggleLayer: (layer: keyof LayerVisibility) => void;
  onTogglePlay: () => void;
  onPlaybackSpeedChange: (speed: number) => void;
  onPauseOnEventChange: (enabled: boolean) => void;
  onStep: (direction: -1 | 1, target: 'event' | 'era') => void;
  onModeChange: (mode: 'explore' | 'guided') => void;
  onLessonStep: (chapterId: string, stepId: string) => void;
  onExport: () => void;
};

export function AtlasPage(props: AtlasPageProps) {
  const { year, panel, onPanelChange, world, selectedId, selectedFeature, detailWorld, layers, backendStatus } = props;
  const drawerRef = useRef<HTMLDivElement>(null);
  const layersButton = useRef<HTMLButtonElement>(null);
  const detailsButton = useRef<HTMLButtonElement>(null);
  const additionalButtons = useRef<Record<string, HTMLButtonElement | null>>({});
  const previousPanel = useRef(panel);
  useEffect(() => {
    if (panel) drawerRef.current?.focus();
    else if (previousPanel.current) (previousPanel.current === 'layers' ? layersButton.current : previousPanel.current === 'details' ? detailsButton.current : additionalButtons.current[previousPanel.current])?.focus();
    previousPanel.current = panel;
    if (!panel) return;
    const escape = (event: KeyboardEvent) => { if (event.key === 'Escape') { event.preventDefault(); onPanelChange(null); } };
    window.addEventListener('keydown', escape);
    return () => window.removeEventListener('keydown', escape);
  }, [panel, onPanelChange]);
  const displayedYear = backendStatus === 'loading' ? world.year : year;
  const sourceCount = world.civilizations.reduce((sum, item) => sum + item.evidence.length, 0);
  const boundaryLayers = detailWorld.layers.filter((layer) => layer.interpretationKind === 'boundary_variant');
  const groups = Array.from(new Set(boundaryLayers.map(boundaryGroup)));
  const chapter = props.chapters.find((item) => item.id === props.chapterId);
  const step = chapter?.steps.find((item) => item.id === props.stepId);

  return <main className="atlas-page immersive-atlas" aria-label="Historical atlas">
    <div className="atlas-stage">
      <div className="atlas-stage-map">{props.map}</div>
      <div className="atlas-view-heading">
        <p className="atlas-kicker">THE HISTORICAL WORLD</p>
        <h1>World at <span>{formatYear(displayedYear)}</span></h1>
        <p className="atlas-view-subtitle">Civilizations, connections, and the evidence between them.</p>
        <div className="atlas-view-status" role="status">
          <span className={`status-dot status-dot--${backendStatus}`} aria-hidden />
          <span>{{ live: 'Published atlas', demo: 'Source snapshot · curated coverage', loading: world.civilizations.length ? `Loading ${formatYear(year)}… Showing ${formatYear(world.year)} until ready.` : 'Loading selected year…', stale: 'Data unavailable', unavailable: 'Database unavailable' }[backendStatus]}</span>
          <span> / {world.civilizations.length} polities</span>
        </div>
      </div>
      <div className="atlas-panel-switches" role="group" aria-label="Research panels">
        <button className="atlas-tool" ref={layersButton} aria-controls="atlas-research-panel" aria-expanded={panel === 'layers'} onClick={() => onPanelChange(panel === 'layers' ? null : 'layers')} type="button">☷ <span>Layers & research</span>{props.filterCount > 0 && <span className="atlas-count">{props.filterCount}</span>}</button>
        <button className="atlas-tool" ref={detailsButton} aria-controls="atlas-research-panel" aria-expanded={panel === 'details'} onClick={() => onPanelChange(panel === 'details' ? null : 'details')} type="button">⌖ <span>Selection & evidence</span></button>
        {(['notes', 'research', 'episodes', 'status'] as const).map((name) => <button className="atlas-tool" key={name} ref={(el) => { additionalButtons.current[name] = el; }} type="button" aria-controls="atlas-research-panel" aria-expanded={panel === name} onClick={() => onPanelChange(panel === name ? null : name)}>{name === 'notes' ? 'Map notes' : name === 'research' ? 'Area query' : name === 'episodes' ? 'Episodes' : 'Layer status'}</button>)}
        <button className="atlas-tool atlas-export" onClick={props.onExport} type="button">Export current view ↗</button>
      </div>
      {(backendStatus === 'unavailable' || props.catalogFailed) && <div className="atlas-data-notice" role="alert"><p>{backendStatus === 'unavailable' ? 'Historical data is unavailable for this year.' : 'The event and source catalog could not be loaded.'}</p><button className="atlas-tool" onClick={props.onRetry} type="button">Retry data</button></div>}
      {backendStatus !== 'loading' && backendStatus !== 'unavailable' && !world.civilizations.length && <div className="atlas-data-notice" role="status">No polities match this date and these filters. Try 117 CE or clear the research filters.</div>}
      <div hidden={!panel} id="atlas-research-panel" ref={drawerRef} tabIndex={-1} className={`atlas-research-drawer atlas-research-drawer--${panel}`} role="region" aria-label={panel === 'layers' ? 'Layers and research' : panel === 'details' ? 'Selection and evidence' : `${panel} workspace`}>
        <div className="atlas-drawer-heading"><h2>{panel === 'layers' ? 'Layers & research' : panel === 'details' ? 'Selection & evidence' : panel === 'notes' ? 'Map notes' : panel === 'research' ? 'Area query' : panel === 'episodes' ? 'Episodes' : 'Layer status'}</h2><button className="atlas-tool" onClick={() => onPanelChange(null)} aria-label="Close research panel" type="button">×</button></div>
        {panel === 'layers' ? <div className="atlas-drawer-content">
          <ActiveCivilizationsPanel civilizations={world.civilizations} selectedId={selectedId} selectedYear={displayedYear} onSelect={props.onCivilizationSelect} />
          <button className="atlas-tool text-left" type="button" aria-pressed={props.showModernBorders} onClick={props.onToggleModernBorders}>Present-day borders · {props.showModernBorders ? 'visible' : 'hidden'}<span className="mt-1 block text-xs text-slate-300">Faint modern reference lines; separate from the historical boundaries.</span></button>
          <LayerControls counts={{ extents: world.civilizations.length, nodes: world.nodes.length, routes: world.routes.length, sources: sourceCount }} onToggle={props.onToggleLayer} values={layers} />
          <AtlasFilters confidenceCounts={props.confidenceCounts} layerTypeOptions={props.layerTypeOptions} onConfidenceToggle={props.onConfidenceToggle} onLayerTypeToggle={props.onLayerTypeToggle} onReset={props.onResetFilters} onReviewStatusToggle={props.onReviewStatusToggle} reviewCounts={props.reviewCounts} selectedConfidence={props.selectedConfidence} selectedLayerTypes={props.selectedLayerTypes} selectedReviewStatus={props.selectedReviewStatus} />
          <section className="atlas-panel rounded-2xl p-4" aria-label="Boundary interpretations"><p className="atlas-kicker">Boundary interpretations</p><p className="mt-2 text-sm text-slate-300">Compare source interpretations. Approximate extents remain approximate.</p>
            {groups.length === 0 && <p className="mt-3 text-sm text-slate-400">No boundary alternatives are available for this date.</p>}
            {groups.map((group) => <fieldset className="mt-4 border-t border-white/10 pt-3" key={group}><legend className="px-1 text-sm font-semibold">{world.civilizations.find((item) => item.id === boundaryLayers.find((layer) => boundaryGroup(layer) === group)?.civilizationId)?.label ?? group}</legend>{boundaryLayers.filter((layer) => boundaryGroup(layer) === group).map((layer) => <label key={layer.id} className="mt-3 block text-sm"><span className="flex items-start gap-2"><input type="checkbox" checked={props.selectedLayerIds.includes(layer.id)} onChange={(event) => props.onBoundaryChange(layer.id, event.target.checked)} /><strong>{layer.interpretationLabel || layer.name}</strong></span><span className="ml-5 mt-1 block text-xs text-slate-400">{layer.confidence.replace('_', ' ')} confidence · {layer.reviewStatus.replace('_', ' ')}</span><span className="ml-5 mt-1 block text-xs leading-5 text-slate-300">{layer.sourceNote}</span>{layer.sourceRecordIds.map((id) => <a className="ml-5 block text-xs text-cyan-200 underline" href={`/sources/${encodeURIComponent(id)}`} key={id}>Source record ↗</a>)}</label>)}</fieldset>)}
          </section>
          <details className="atlas-panel rounded-2xl p-4"><summary>Map information as a table</summary><div className="mt-3 overflow-x-auto"><table className="text-left text-sm"><caption className="sr-only">Visible polity extent descriptions</caption><thead><tr><th>Polity</th><th>Dates</th><th>Evidence</th></tr></thead><tbody>{world.civilizations.map((item) => <tr key={item.id}><th scope="row">{item.label}</th><td>{formatYear(item.startYear)}–{formatYear(item.endYear)}</td><td>{item.extentNote}<br />{item.confidence.replace('_', ' ')} · {item.reviewStatus.replace('_', ' ')}</td></tr>)}</tbody></table></div></details>
        </div> : panel === 'details' ? <DetailPanel feature={selectedFeature} isFilteredOut={props.isSelectedFeatureFilteredOut} world={detailWorld} /> : null}
        <div hidden={panel !== 'notes'}>{props.notesContent}</div>
        <div hidden={panel !== 'research'}>{props.researchContent}</div>
        <div hidden={panel !== 'episodes'}>{props.episodesContent}</div>
        <div hidden={panel !== 'status'}>{props.statusContent}</div>
      </div>
      <div className="atlas-stage-caption"><span>EXPLORE THE PAST</span><span>{props.showModernBorders ? 'Faint modern borders · approximate historical layers' : 'Modern basemap · approximate historical layers'}</span></div>
    </div>
    <div className="atlas-time-dock">
      <div className="atlas-experience-bar"><span className="atlas-kicker">TIME EXPLORER</span><div role="group" aria-label="Atlas mode">{(['explore', 'guided'] as const).map((mode) => <button type="button" key={mode} aria-pressed={props.mode === mode} onClick={() => props.onModeChange(mode)}>{mode === 'explore' ? 'Free exploration' : 'Guided lesson'}</button>)}</div></div>
      {props.mode === 'guided' && chapter && step && <section className="atlas-guided-compact" aria-label="Guided lesson"><div><p className="atlas-kicker">{chapter.title}</p><h2 className="mt-2 text-lg">{step.title}</h2><p className="mt-2 text-sm text-slate-300">{step.narrative}</p></div><div className="flex flex-wrap gap-2">{chapter.steps.map((item, index) => <button className="atlas-tool" type="button" aria-pressed={item.id === step.id} key={item.id} onClick={() => props.onLessonStep(chapter.id, item.id)}>{index + 1}. {item.title}</button>)}</div><details><summary>Annotations & source prompt</summary>{step.annotations.map((note) => <p className="mt-2 text-sm" key={note}>{note}</p>)}<p className="mt-2 text-sm">{step.question}</p><p className="mt-2 text-sm text-cyan-100">{step.sourcePrompt}</p></details></section>}
      <TimelineControl eras={props.eras} events={props.events} isPlaying={props.isPlaying} year={year} onTogglePlay={props.onTogglePlay} playbackSpeed={props.playbackSpeed} pauseOnEvent={props.pauseOnEvent} reducedMotion={props.reducedMotion} onPlaybackSpeedChange={props.onPlaybackSpeedChange} onPauseOnEventChange={props.onPauseOnEventChange} onStep={props.onStep} onYearChange={props.onYearChange} />
    </div>
  </main>;
}
