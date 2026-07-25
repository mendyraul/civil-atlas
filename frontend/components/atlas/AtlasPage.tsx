import { StatusBadge } from '../badges/StatusBadge';
import { ActiveCivilizationsPanel } from './ActiveCivilizationsPanel';
import { AtlasFilters, type LayerTypeOption } from './AtlasFilters';
import { LayerControls } from './LayerControls';
import { DetailPanel } from './DetailPanel';
import { TimelineControl } from '../timeline/TimelineControl';
import { featureBadgeTone, formatYear } from '../../lib/atlas';
import type { AtlasFeature, Confidence, Era, HistoricalEvent, ReviewStatus, WorldPayload } from '../../types/atlas';

type LayerVisibility = {
  extents: boolean;
  nodes: boolean;
  routes: boolean;
  sources: boolean;
};

type AtlasPageProps = {
  year: number;
  zoom: number;
  backendStatus: 'seed' | 'live';
  confidenceCounts: Record<Confidence, number>;
  detailWorld: WorldPayload;
  eras: Era[];
  events: HistoricalEvent[];
  filterCount: number;
  isPlaying: boolean;
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
}: AtlasPageProps) {
  const sourceCount = world.civilizations.reduce((total, civilization) => total + civilization.evidence.length, 0);
  const badges = ['Approximate', 'Source-reported', 'Needs review'] as const;

  return (
    <div className="flex min-h-[calc(100vh-3rem)] flex-col gap-5">
      <section className="atlas-hero rounded-[32px] px-5 py-5 md:px-6">
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
                {backendStatus === 'live' ? 'FastAPI live' : 'Seed fallback'}
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

      <main className="grid min-h-0 flex-1 grid-cols-1 gap-5 xl:grid-cols-[320px_minmax(0,1fr)_360px]">
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
        </section>

        <DetailPanel
          feature={selectedFeature}
          isFilteredOut={filterCount > 0 && isSelectedFeatureFilteredOut}
          world={detailWorld}
        />
      </main>

      <TimelineControl
        eras={eras}
        events={events}
        isPlaying={isPlaying}
        year={year}
        onTogglePlay={onTogglePlay}
        onYearChange={onYearChange}
      />
    </div>
  );
}
