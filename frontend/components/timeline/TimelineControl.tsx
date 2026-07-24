import { confidenceLabel, evidenceTone, formatYear, reviewLabel, reviewTone, YEAR_MAX, YEAR_MIN } from '../../lib/atlas';
import { StatusBadge } from '../badges/StatusBadge';
import type { Era, HistoricalEvent } from '../../types/atlas';

type TimelineControlProps = {
  eras: Era[];
  events: HistoricalEvent[];
  year: number;
  onYearChange: (year: number) => void;
};

const PRESETS = [-500, 0, 117, 700, 1500];

export function TimelineControl({ eras, events, year, onYearChange }: TimelineControlProps) {
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
      <div className="mt-5 grid gap-4 xl:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)]">
        <div className="rounded-[24px] border border-white/8 bg-black/14 p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="atlas-kicker">Active eras</p>
              <h3 className="mt-2 text-lg font-semibold text-white">{eras.length} contextual frames</h3>
            </div>
            <span className="rounded-full border border-white/10 px-3 py-1 text-xs text-slate-400">
              At {formatYear(year)}
            </span>
          </div>
          <div className="mt-4 flex flex-col gap-3">
            {eras.map((era) => (
              <article className="rounded-[20px] border border-white/8 bg-white/4 p-4" key={era.id}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h4 className="text-sm font-semibold text-white">{era.label}</h4>
                    <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">
                      {formatYear(era.startYear)} to {formatYear(era.endYear)} · {era.focusRegion}
                    </p>
                  </div>
                  <span className={`rounded-full px-2.5 py-1 text-xs ${evidenceTone(era.confidence)}`}>
                    {confidenceLabel(era.confidence)}
                  </span>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-300">{era.summary}</p>
              </article>
            ))}
          </div>
        </div>
        <div className="rounded-[24px] border border-white/8 bg-black/14 p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="atlas-kicker">Historical log</p>
              <h3 className="mt-2 text-lg font-semibold text-white">Nearby changes and turning points</h3>
            </div>
            <span className="rounded-full border border-white/10 px-3 py-1 text-xs text-slate-400">
              {events.length} events
            </span>
          </div>
          <div className="mt-4 flex flex-col gap-3">
            {events.map((event) => (
              <article className="rounded-[20px] border border-white/8 bg-white/4 p-4" key={event.id}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h4 className="text-sm font-semibold text-white">{event.label}</h4>
                    <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">
                      {event.displayDate} · {event.eventType.replace('_', ' ')}
                    </p>
                  </div>
                  <StatusBadge label={reviewLabel(event.reviewStatus)} tone={reviewTone(event.reviewStatus)} />
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-300">{event.summary}</p>
                <p className="mt-3 text-sm leading-6 text-slate-400">{event.impact}</p>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
