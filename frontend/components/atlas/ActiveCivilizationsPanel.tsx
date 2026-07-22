import { formatYear } from '../../lib/atlas';
import type { Civilization } from '../../types/atlas';

type ActiveCivilizationsPanelProps = {
  civilizations: Civilization[];
  selectedId?: string;
  selectedYear: number;
  onSelect: (id: string) => void;
};

export function ActiveCivilizationsPanel({
  civilizations,
  selectedId,
  selectedYear,
  onSelect,
}: ActiveCivilizationsPanelProps) {
  return (
    <section className="atlas-panel rounded-[28px] p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="atlas-kicker">Active civilizations</p>
          <h2 className="mt-2 text-lg font-semibold text-white">
            {civilizations.length} visible in {formatYear(selectedYear)}
          </h2>
        </div>
        <div className="rounded-full border border-white/12 bg-white/6 px-3 py-1 text-xs uppercase tracking-[0.2em] text-slate-300">
          Seed model
        </div>
      </div>

      <div className="mt-4 flex flex-col gap-3">
        {civilizations.map((civilization) => {
          const isSelected = selectedId === civilization.id;
          return (
            <button
              className={`rounded-[22px] border px-4 py-4 text-left transition ${
                isSelected
                  ? 'border-white/18 bg-white/[0.08] shadow-[0_16px_32px_rgba(0,0,0,0.26)]'
                  : 'border-white/8 bg-black/10 hover:border-white/14 hover:bg-white/[0.04]'
              }`}
              key={civilization.id}
              onClick={() => onSelect(civilization.id)}
              type="button"
            >
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-3">
                    <span
                      className="h-3 w-3 rounded-full shadow-[0_0_18px_currentColor]"
                      style={{ backgroundColor: civilization.color, color: civilization.color }}
                    />
                    <span className="truncate font-medium text-white">{civilization.displayName}</span>
                  </div>
                  <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-400">
                    {civilization.civilizationType}
                  </p>
                </div>
                <span className="text-xs text-slate-400">
                  {formatYear(civilization.startYear)} to {formatYear(civilization.endYear)}
                </span>
              </div>
              <p className="mt-3 line-clamp-2 text-sm leading-6 text-slate-300">
                {civilization.shortDescription}
              </p>
              <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
                <span>Capital: {civilization.capital}</span>
                <span>{civilization.evidence.length} evidence records</span>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}
