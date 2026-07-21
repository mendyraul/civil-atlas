import { formatYear, YEAR_MAX, YEAR_MIN } from '../../lib/atlas';

type TimelineControlProps = {
  year: number;
  onYearChange: (year: number) => void;
};

const PRESETS = [-500, 0, 117, 700, 1500];

export function TimelineControl({ year, onYearChange }: TimelineControlProps) {
  return (
    <div className="atlas-panel rounded-[24px] p-5">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">Timeline</h2>
        <span className="text-sm text-[--muted]">{formatYear(year)}</span>
      </div>
      <input
        aria-label="Year"
        className="mt-4 w-full accent-[var(--accent)]"
        max={YEAR_MAX}
        min={YEAR_MIN}
        onChange={(event) => onYearChange(Number(event.target.value))}
        step={1}
        type="range"
        value={year}
      />
      <div className="mt-2 flex justify-between text-xs text-[--muted]">
        <span>600 BCE</span>
        <span>117 CE</span>
        <span>1800 CE</span>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {PRESETS.map((preset) => (
          <button
            className={`rounded-full border px-3 py-2 text-sm transition ${
              preset === year
                ? 'border-slate-900 bg-slate-900 text-amber-50'
                : 'border-slate-300 bg-white/80'
            }`}
            key={preset}
            onClick={() => onYearChange(preset)}
            type="button"
          >
            {formatYear(preset)}
          </button>
        ))}
      </div>
    </div>
  );
}
