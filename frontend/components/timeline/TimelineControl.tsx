'use client';

import { useState } from 'react';
import { confidenceLabel, evidenceTone, formatYear, reviewLabel, reviewTone, YEAR_MAX, YEAR_MIN } from '../../lib/atlas';
import { StatusBadge } from '../badges/StatusBadge';
import type { Era, HistoricalEvent } from '../../types/atlas';

type TimelineControlProps = {
  eras: Era[];
  events: HistoricalEvent[];
  isPlaying: boolean;
  year: number;
  playbackSpeed: number;
  pauseOnEvent: boolean;
  reducedMotion: boolean;
  onPlaybackSpeedChange: (speed: number) => void;
  onPauseOnEventChange: (enabled: boolean) => void;
  onStep: (direction: -1 | 1, target: 'event' | 'era') => void;
  onTogglePlay: () => void;
  onYearChange: (year: number) => void;
};

const PRESETS = [-500, 0, 117, 700, 1500];

const yearToPercent = (value: number) =>
  ((Math.min(Math.max(value, YEAR_MIN), YEAR_MAX) - YEAR_MIN) / (YEAR_MAX - YEAR_MIN)) * 100;

export function TimelineControl({
  eras,
  events,
  isPlaying,
  year,
  playbackSpeed,
  pauseOnEvent,
  reducedMotion,
  onPlaybackSpeedChange,
  onPauseOnEventChange,
  onStep,
  onTogglePlay,
  onYearChange,
}: TimelineControlProps) {
  const [copied, setCopied] = useState(false);

  async function handleShare() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  return (
    <section className="atlas-panel rounded-[30px] px-5 py-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="atlas-kicker">Timeline / playback</p>
          <h2 className="mt-2 text-xl font-semibold text-white">{formatYear(year)}</h2>
          <p className="mt-2 text-sm text-slate-400">Space plays or pauses; ←/→ step through events; Shift + ←/→ step through eras.</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            aria-pressed={isPlaying}
            className={`rounded-full border px-5 py-2 text-sm font-medium transition ${
              isPlaying
                ? 'border-amber-300/50 bg-amber-400/16 text-amber-100'
                : 'border-cyan-300/50 bg-cyan-400/16 text-cyan-100 hover:bg-cyan-400/24'
            }`}
            onClick={onTogglePlay}
            type="button"
          >
            {isPlaying ? '❚❚ Pause' : '▶ Play'}
          </button>
          <button
            className="rounded-full border border-white/10 bg-white/6 px-4 py-2 text-sm text-slate-200 transition hover:border-white/20 hover:text-white"
            onClick={handleShare}
            type="button"
          >
            {copied ? 'Link copied' : 'Share view'}
          </button>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-2" aria-label="Playback settings">
        <span className="text-xs uppercase tracking-[0.16em] text-slate-500">Speed</span>
        {[0.5, 1, 2, 4].map((speed) => (
          <button className={`rounded-full border px-3 py-1.5 text-xs ${playbackSpeed === speed ? 'border-cyan-300/60 bg-cyan-400/14 text-white' : 'border-white/10 text-slate-300'}`} key={speed} onClick={() => onPlaybackSpeedChange(speed)} type="button">{speed}×</button>
        ))}
        <label className="ml-2 flex items-center gap-2 text-sm text-slate-300">
          <input checked={pauseOnEvent} onChange={(event) => onPauseOnEventChange(event.target.checked)} type="checkbox" /> Pause on events
        </label>
        {reducedMotion && <span className="rounded-full border border-amber-300/30 px-3 py-1 text-xs text-amber-100">Reduced motion: autoplay disabled</span>}
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <button className="rounded-full border border-white/10 px-3 py-2 text-sm text-slate-300" onClick={() => onStep(-1, 'era')} type="button">← Era</button>
        <button className="rounded-full border border-white/10 px-3 py-2 text-sm text-slate-300" onClick={() => onStep(-1, 'event')} type="button">← Event</button>
        <button className="rounded-full border border-white/10 px-3 py-2 text-sm text-slate-300" onClick={() => onStep(1, 'event')} type="button">Event →</button>
        <button className="rounded-full border border-white/10 px-3 py-2 text-sm text-slate-300" onClick={() => onStep(1, 'era')} type="button">Era →</button>
      </div>
      <div className="relative mt-5 h-6" aria-hidden>
        {eras.map((era) => (
          <div
            className="absolute top-0 h-2 rounded-full bg-cyan-400/15"
            key={era.id}
            style={{
              left: `${yearToPercent(era.startYear)}%`,
              width: `${Math.max(yearToPercent(era.endYear) - yearToPercent(era.startYear), 0.5)}%`,
            }}
            title={`${era.label} (${formatYear(era.startYear)} to ${formatYear(era.endYear)})`}
          />
        ))}
        {events.map((event) => (
          <button
            aria-label={`Jump to ${event.label} (${event.displayDate})`}
            className="absolute bottom-0 h-4 w-[2px] -translate-x-1/2 rounded-full bg-amber-300/80 transition hover:h-5 hover:bg-amber-200"
            key={event.id}
            onClick={() => onYearChange(event.startYear)}
            style={{ left: `${yearToPercent(event.startYear)}%` }}
            title={`${event.label} · ${event.displayDate}`}
            type="button"
          />
        ))}
      </div>
      <input
        aria-label="Year"
        className="atlas-range mt-1 w-full"
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
                <div className="mt-3 rounded-xl border border-amber-300/15 bg-amber-300/5 p-3 text-xs leading-5 text-amber-50/80">
                  <strong>Why the map changes:</strong> {event.transitionClaim ?? event.label}.{' '}
                  {event.dateUncertainty ?? (event.startYear === event.endYear ? 'The source tradition assigns this change to a specific year.' : `This is an interval estimate between ${formatYear(event.startYear)} and ${formatYear(event.endYear)}; the map changes within a process, not at one certain instant.`)}
                </div>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
