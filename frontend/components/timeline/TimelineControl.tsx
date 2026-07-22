import { formatYear, YEAR_MAX, YEAR_MIN } from '../../lib/atlas';

type TimelineControlProps = {
  year: number;
  onYearChange: (year: number) => void;
};

const PRESETS = [-500, 0, 117, 700, 1500];

export function TimelineControl({ year, onYearChange }: TimelineControlProps) {
  return (
    <section className="atlas-panel rounded-[30px] px-5 py-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="atlas-kicker">Timeline / playback</p>
          <h2 className="mt-2 text-xl font-semibold text-white">{formatYear(year)}</h2>
          <p className="mt-2 text-sm text-slate-400">
            Timeline defaults to 117 CE and drives active civilizations across the atlas.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            className="rounded-full border border-white/10 bg-white/6 px-4 py-2 text-sm text-slate-200"
            type="button"
          >
            Play
          </button>
          <div className="rounded-full border border-white/10 px-4 py-2 text-sm text-slate-400">
            Placeholder playback
          </div>
        </div>
      </div>
      <input
        aria-label="Year"
        className="atlas-range mt-5 w-full"
        max={YEAR_MAX}
        min={YEAR_MIN}
        onChange={(event) => onYearChange(Number(event.target.value))}
        step={1}
        type="range"
        value={year}
      />
      <div className="mt-2 flex justify-between text-xs text-slate-500">
        <span>600 BCE</span>
        <span>117 CE</span>
        <span>1800 CE</span>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {PRESETS.map((preset) => (
          <button
            className={`rounded-full border px-3 py-2 text-sm transition ${
              preset === year
                ? 'border-cyan-300/60 bg-cyan-400/14 text-white'
                : 'border-white/10 bg-white/6 text-slate-300 hover:border-white/16 hover:text-white'
            }`}
            key={preset}
            onClick={() => onYearChange(preset)}
            type="button"
          >
            {formatYear(preset)}
          </button>
        ))}
      </div>
    </section>
  );
}
