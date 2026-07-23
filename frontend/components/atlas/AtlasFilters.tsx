import { confidenceLabel, reviewLabel } from '../../lib/atlas';
import type { Confidence, ReviewStatus } from '../../types/atlas';

export type LayerTypeOption = {
  count: number;
  group: 'civilization' | 'node' | 'route';
  label: string;
  value: string;
};

type AtlasFiltersProps = {
  confidenceCounts: Record<Confidence, number>;
  layerTypeOptions: LayerTypeOption[];
  reviewCounts: Record<ReviewStatus, number>;
  selectedConfidence: Confidence[];
  selectedLayerTypes: string[];
  selectedReviewStatus: ReviewStatus[];
  onConfidenceToggle: (value: Confidence) => void;
  onLayerTypeToggle: (value: string) => void;
  onReset: () => void;
  onReviewStatusToggle: (value: ReviewStatus) => void;
};

const reviewOrder: ReviewStatus[] = ['reviewed', 'seeded', 'needs_review', 'placeholder'];
const confidenceOrder: Confidence[] = ['high', 'medium_high', 'medium', 'low'];

const groupLabels: Record<LayerTypeOption['group'], string> = {
  civilization: 'Polity layers',
  node: 'Place roles',
  route: 'Route types',
};

type FilterChipProps = {
  count: number;
  isActive: boolean;
  label: string;
  onClick: () => void;
};

function FilterChip({ count, isActive, label, onClick }: FilterChipProps) {
  return (
    <button
      className={`rounded-full border px-3 py-2 text-sm transition ${
        isActive
          ? 'border-cyan-300/50 bg-cyan-400/12 text-white'
          : 'border-white/10 bg-black/10 text-slate-300 hover:border-white/18 hover:bg-white/[0.04]'
      }`}
      onClick={onClick}
      type="button"
    >
      <span>{label}</span>
      <span className="ml-2 rounded-full border border-white/10 px-2 py-0.5 text-[11px] text-slate-400">
        {count}
      </span>
    </button>
  );
}

export function AtlasFilters({
  confidenceCounts,
  layerTypeOptions,
  reviewCounts,
  selectedConfidence,
  selectedLayerTypes,
  selectedReviewStatus,
  onConfidenceToggle,
  onLayerTypeToggle,
  onReset,
  onReviewStatusToggle,
}: AtlasFiltersProps) {
  const activeCount =
    selectedLayerTypes.length + selectedReviewStatus.length + selectedConfidence.length;
  const groups = (Object.keys(groupLabels) as LayerTypeOption['group'][]).map((group) => ({
    group,
    options: layerTypeOptions.filter((option) => option.group === group),
  }));

  return (
    <section className="atlas-panel rounded-[28px] p-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="atlas-kicker">Atlas filters</p>
          <h2 className="mt-2 text-lg font-semibold text-white">Evidence-aware controls</h2>
        </div>
        <button
          className="rounded-full border border-white/10 px-3 py-1 text-xs uppercase tracking-[0.18em] text-slate-300 transition hover:border-white/20 hover:text-white"
          disabled={activeCount === 0}
          onClick={onReset}
          type="button"
        >
          Reset {activeCount > 0 ? `(${activeCount})` : ''}
        </button>
      </div>

      <div className="mt-5 space-y-5">
        {groups.map(({ group, options }) =>
          options.length > 0 ? (
            <div key={group}>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{groupLabels[group]}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {options.map((option) => (
                  <FilterChip
                    count={option.count}
                    isActive={selectedLayerTypes.includes(option.value)}
                    key={option.value}
                    label={option.label}
                    onClick={() => onLayerTypeToggle(option.value)}
                  />
                ))}
              </div>
            </div>
          ) : null,
        )}

        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Review status</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {reviewOrder.map((status) => (
              <FilterChip
                count={reviewCounts[status]}
                isActive={selectedReviewStatus.includes(status)}
                key={status}
                label={reviewLabel(status)}
                onClick={() => onReviewStatusToggle(status)}
              />
            ))}
          </div>
        </div>

        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Confidence</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {confidenceOrder.map((confidence) => (
              <FilterChip
                count={confidenceCounts[confidence]}
                isActive={selectedConfidence.includes(confidence)}
                key={confidence}
                label={confidenceLabel(confidence)}
                onClick={() => onConfidenceToggle(confidence)}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
