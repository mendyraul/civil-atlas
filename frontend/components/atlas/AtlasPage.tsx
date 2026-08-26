import { StatusBadge } from '../badges/StatusBadge';
import { ActiveCivilizationsPanel } from './ActiveCivilizationsPanel';
import { AtlasFilters, type LayerTypeOption } from './AtlasFilters';
import { LayerControls } from './LayerControls';
import { DetailPanel } from './DetailPanel';
import { TimelineControl } from '../timeline/TimelineControl';
import { featureBadgeTone, formatYear } from '../../lib/atlas';
import type { AtlasFeature, Confidence, Era, HistoricalEvent, LearningChapter, ReviewStatus, WorldPayload } from '../../types/atlas';

type LayerVisibility = {
  extents: boolean;
  nodes: boolean;
  routes: boolean;
  sources: boolean;
};

type AtlasPageProps = {
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
  onToggleLayer: (layer: keyof LayerVisibility) => void;
  onTogglePlay: () => void;
  onPlaybackSpeedChange: (speed: number) => void;
  onPauseOnEventChange: (enabled: boolean) => void;
  onStep: (direction: -1 | 1, target: 'event' | 'era') => void;
  onModeChange: (mode: 'explore' | 'guided') => void;
  onLessonStep: (chapterId: string, stepId: string) => void;
};

export function AtlasPage({
  year,
  zoom,
  backendStatus,
  confidenceCounts,
  detailWorld,
  eras,
  events,
  filterCount,
  isPlaying,
  isSelectedFeatureFilteredOut,
  layerTypeOptions,
  reviewCounts,
  selectedId,
  selectedConfidence,
  selectedFeature,
  selectedLayerTypes,
  selectedReviewStatus,
  world,
  layers,
  map,
  onConfidenceToggle,
  onYearChange,
  onCivilizationSelect,
  onLayerTypeToggle,
  onResetFilters,
  onReviewStatusToggle,
  onToggleLayer,
  onTogglePlay,
  playbackSpeed, pauseOnEvent, reducedMotion, onPlaybackSpeedChange, onPauseOnEventChange, onStep,
  chapters, chapterId, stepId, mode, onModeChange, onLessonStep,
}: AtlasPageProps) {
  const sourceCount = world.civilizations.reduce((total, civilization) => total + civilization.evidence.length, 0);
  const badges = ['Approximate', 'Source-reported', 'Needs review'] as const;

  return (
    <main className="flex min-h-[calc(100vh-3rem)] flex-col gap-5">
      <section className="atlas-hero rounded-[32px] px-5 py-5 md:px-6">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-[22px] border border-white/10 bg-black/16 p-3">
          <div><p className="atlas-kicker">Experience</p><p className="mt-1 text-sm text-slate-300">Choose a curated path or keep every research control available.</p></div>
          <div className="flex rounded-full border border-white/10 p-1" role="group" aria-label="Atlas mode">
            {(['explore', 'guided'] as const).map((option) => <button aria-pressed={mode === option} className={`rounded-full px-4 py-2 text-sm capitalize ${mode === option ? 'bg-cyan-400/18 text-cyan-50' : 'text-slate-400'}`} key={option} onClick={() => onModeChange(option)} type="button">{option === 'guided' ? 'Guided lesson' : 'Explore'}</button>)}
          </div>
        </div>
        <div className="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
          <div className="max-w-3xl">
            <p className="atlas-kicker">Civil Atlas</p>
            <div className="mt-3 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <h1 className="font-serif text-4xl tracking-[-0.05em] text-white md:text-6xl">
                  Explore civilizations through time
                </h1>
                <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300 md:text-base">
                  A map-first historical dashboard for time-aware polities, routes, places, and evidence.
                  The visual language favors provenance and uncertainty over fake certainty.
                </p>
              </div>
            </div>
          </div>

          <div className="grid gap-3 md:grid-cols-3 xl:w-[420px] xl:grid-cols-1">
            <div className="rounded-[24px] border border-white/10 bg-black/16 px-4 py-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Selected year</p>
              <p className="mt-3 text-3xl font-semibold text-white">{formatYear(year)}</p>
            </div>
            <div className="rounded-[24px] border border-white/10 bg-black/16 px-4 py-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Visible polities</p>
              <p className="mt-3 text-3xl font-semibold text-white">{world.civilizations.length}</p>
            </div>
            <div className="rounded-[24px] border border-white/10 bg-black/16 px-4 py-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Data channel</p>
              <p className="mt-3 text-xl font-semibold text-white">
                {{ live: 'Database live', demo: 'Demo snapshot', loading: 'Loading database', stale: 'Database stale', unavailable: 'Database unavailable' }[backendStatus]}
              </p>
            </div>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-2">
          {badges.map((badge) => (
            <StatusBadge key={badge} label={badge} tone={featureBadgeTone(badge)} />
          ))}
          <span className="rounded-full border border-white/10 px-3 py-1 text-xs text-slate-400">
            Zoom {zoom.toFixed(1)}x
          </span>
          <span className="rounded-full border border-white/10 px-3 py-1 text-xs text-slate-400">
            {sourceCount} civilization evidence records
          </span>
        </div>
      </section>

      {mode === 'guided' && chapters.map((chapter) => chapter.id === chapterId && (
        <section className="atlas-panel rounded-[30px] p-5" key={chapter.id}>
          <p className="atlas-kicker">Guided lesson · resumable link</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">{chapter.title}</h2>
          <p className="mt-2 text-sm text-slate-300">{chapter.summary}</p>
          <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-400">{chapter.objectives.map((objective) => <li key={objective}>{objective}</li>)}</ul>
          <div className="mt-5 grid gap-3 md:grid-cols-3">{chapter.steps.map((step, index) => (
            <button className={`rounded-[20px] border p-4 text-left ${step.id === stepId ? 'border-cyan-300/50 bg-cyan-400/10' : 'border-white/10 bg-white/4'}`} key={step.id} onClick={() => onLessonStep(chapter.id, step.id)} type="button">
              <span className="text-xs uppercase tracking-[0.16em] text-slate-500">Step {index + 1}</span><strong className="mt-2 block text-white">{step.title}</strong><span className="mt-2 block text-sm leading-6 text-slate-300">{step.narrative}</span>
            </button>
          ))}</div>
          {chapter.steps.map((step) => step.id === stepId && <div className="mt-4 grid gap-3 lg:grid-cols-2" key={step.id}><div className="rounded-2xl border border-amber-300/15 bg-amber-300/5 p-4"><p className="text-sm font-semibold text-amber-100">Annotations</p>{step.annotations.map((note) => <p className="mt-2 text-sm text-slate-300" key={note}>• {note}</p>)}</div><div className="rounded-2xl border border-white/10 p-4"><p className="text-sm text-white">{step.question}</p><p className="mt-3 text-xs leading-5 text-cyan-100"><strong>Source prompt:</strong> {step.sourcePrompt}</p></div></div>)}
        </section>
      ))}

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-5 xl:grid-cols-[320px_minmax(0,1fr)_360px]">
        <section className="flex min-h-0 flex-col gap-5">
          <ActiveCivilizationsPanel
            civilizations={world.civilizations}
            selectedId={selectedId}
            selectedYear={year}
            onSelect={onCivilizationSelect}
          />
          <LayerControls
            counts={{
              extents: world.civilizations.length,
              nodes: world.nodes.length,
              routes: world.routes.length,
              sources: sourceCount,
            }}
            onToggle={onToggleLayer}
            values={layers}
          />
          <AtlasFilters
            confidenceCounts={confidenceCounts}
            layerTypeOptions={layerTypeOptions}
            onConfidenceToggle={onConfidenceToggle}
            onLayerTypeToggle={onLayerTypeToggle}
            onReset={onResetFilters}
            onReviewStatusToggle={onReviewStatusToggle}
            reviewCounts={reviewCounts}
            selectedConfidence={selectedConfidence}
            selectedLayerTypes={selectedLayerTypes}
            selectedReviewStatus={selectedReviewStatus}
          />
        </section>

        <section className="atlas-map-shell overflow-hidden rounded-[30px]">
          <div className="border-b border-white/10 px-5 py-4">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="atlas-kicker">Atlas viewport</p>
                <h2 className="mt-2 text-xl font-semibold text-white">
                  World at {formatYear(year)}
                </h2>
              </div>
              <div className="flex flex-wrap gap-2 text-xs text-slate-400">
                <span className="rounded-full border border-white/10 px-3 py-1">
                  Map-first dashboard
                </span>
                <span className="rounded-full border border-white/10 px-3 py-1">
                  Routes: {world.routes.length}
                </span>
                <span className="rounded-full border border-white/10 px-3 py-1">
                  Nodes: {world.nodes.length}
                </span>
              </div>
            </div>
          </div>
          <div className="relative">{map}</div>
          <details className="border-t border-white/10 p-5" open>
            <summary className="cursor-pointer font-semibold text-cyan-200">Map information as a table</summary>
            <p className="mt-2 text-sm text-slate-300" aria-live="polite">Active layers: {layers.extents ? 'polity extents, ' : ''}{layers.nodes ? 'places, ' : ''}{layers.routes ? 'routes, ' : ''}{layers.sources ? 'evidence' : ''}. Symbols use outlines, dashed routes, and point shapes in addition to color.</p>
            <div className="mt-3 overflow-x-auto"><table className="w-full text-left text-sm"><caption className="sr-only">Visible polity extent descriptions</caption><thead><tr><th className="p-2">Polity</th><th className="p-2">Dates</th><th className="p-2">Narrative extent</th><th className="p-2">Evidence</th></tr></thead><tbody>{world.civilizations.map((item) => <tr className="border-t border-white/10" key={item.id}><th scope="row" className="p-2">{item.label}</th><td className="p-2">{formatYear(item.startYear)}–{formatYear(item.endYear)}</td><td className="p-2">{item.extentNote}</td><td className="p-2">{item.confidence.replace('_', ' ')}, {item.reviewStatus.replace('_', ' ')}</td></tr>)}</tbody></table></div>
          </details>
        </section>

        <DetailPanel
          feature={selectedFeature}
          isFilteredOut={filterCount > 0 && isSelectedFeatureFilteredOut}
          world={detailWorld}
        />
      </div>

      <TimelineControl
        eras={eras}
        events={events}
        isPlaying={isPlaying}
        year={year}
        onTogglePlay={onTogglePlay}
        playbackSpeed={playbackSpeed}
        pauseOnEvent={pauseOnEvent}
        reducedMotion={reducedMotion}
        onPlaybackSpeedChange={onPlaybackSpeedChange}
        onPauseOnEventChange={onPauseOnEventChange}
        onStep={onStep}
        onYearChange={onYearChange}
      />
    </main>
  );
}
