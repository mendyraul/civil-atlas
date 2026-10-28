import type { FeatureCollection, Geometry } from 'geojson';

export type BoundaryData = FeatureCollection<Geometry>;
export const BOUNDARY_FADE_MS = 240;

/** Cross-fade complete source snapshots, never interpolate historical coordinates. */
export function createBoundaryTransition(target: {
  write: (data: BoundaryData) => void;
  paint: (progress: number, generation: number) => void;
  ready: () => boolean;
}) {
  let current: BoundaryData = { type: 'FeatureCollection', features: [] };
  let desired = current;
  let incoming = current;
  let waiting = false;
  let busy = false;
  let disposed = false;
  let frame = 0;
  let generation = 0;

  function start(next: BoundaryData, animate: boolean) {
    if (disposed) return;
    desired = next;
    // Explicitly empty selections (filters, missing coverage or failures) clear
    // immediately. Reduced motion never leaves an animation queued.
    if (!animate || !current.features.length || !next.features.length) {
      cancelAnimationFrame(frame);
      busy = waiting = false;
      current = incoming = next;
      target.paint(1, generation);
      target.write(next);
      return;
    }
    if (busy || current === next) return;
    incoming = next;
    busy = waiting = true;
    generation += 1;
    // A new generation lets old tiles retain their settled appearance while
    // replacement tiles arrive, with the new incoming features still invisible.
    target.paint(0, generation);
    const unchanged = new Set(next.features.filter((feature) => current.features.some((old) => old.id === feature.id && old.geometry === feature.geometry)).map((feature) => feature.id));
    target.write({ type: 'FeatureCollection', features: [
      ...current.features.filter((feature) => !unchanged.has(feature.id)).map((feature) => ({
        ...feature, id: `outgoing:${feature.id}`, properties: { ...feature.properties, id: `outgoing:${feature.id}`, timelineRole: -1, timelineGeneration: generation },
      })),
      ...next.features.map((feature) => unchanged.has(feature.id) ? feature : ({ ...feature, properties: { ...feature.properties, timelineRole: 1, timelineGeneration: generation } })),
    ] });
  }

  function sourceReady() {
    if (disposed || !waiting || !target.ready()) return;
    waiting = false;
    target.paint(0, generation);
    // Start only after the worker has installed BOTH snapshots. The previous
    // features remain fully opaque throughout source parsing and fast drags.
    let began: number | undefined;
    const tick = (now: number) => {
      if (disposed) return;
      began ??= now;
      const progress = Math.min((now - began) / BOUNDARY_FADE_MS, 1);
      target.paint(progress * progress * (3 - 2 * progress), generation);
      if (progress < 1) frame = requestAnimationFrame(tick);
      else {
        current = incoming;
        busy = false;
        if (desired !== current) start(desired, true);
        else target.write(current);
      }
    };
    frame = requestAnimationFrame(tick);
  }

  return {
    update: start,
    sourceReady,
    dispose: () => { disposed = true; cancelAnimationFrame(frame); },
  };
}
