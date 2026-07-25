'use client';

type LegendCivilization = {
  id: string;
  label: string;
  color: string;
};

type MapLegendProps = {
  civilizations: LegendCivilization[];
  showExtents: boolean;
  showNodes: boolean;
  showRoutes: boolean;
};

export function MapLegend({
  civilizations,
  showExtents,
  showNodes,
  showRoutes,
}: MapLegendProps) {
  const hasContent = civilizations.length > 0 || showNodes || showRoutes;
  if (!hasContent) return null;

  return (
    <div className="pointer-events-none absolute bottom-4 left-4 z-10 max-w-[240px]">
      <div className="pointer-events-auto rounded-2xl border border-white/10 bg-black/55 px-4 py-3 text-xs text-slate-200 shadow-[0_8px_30px_rgba(0,0,0,0.45)] backdrop-blur-md">
        <p className="text-[10px] uppercase tracking-[0.18em] text-slate-400">Legend</p>

        {showExtents && civilizations.length > 0 && (
          <ul className="mt-2 flex max-h-40 flex-col gap-1.5 overflow-y-auto pr-1">
            {civilizations.map((civilization) => (
              <li key={civilization.id} className="flex items-center gap-2">
                <span
                  aria-hidden
                  className="h-2.5 w-2.5 flex-none rounded-[3px]"
                  style={{ backgroundColor: civilization.color }}
                />
                <span className="truncate text-slate-100">{civilization.label}</span>
              </li>
            ))}
          </ul>
        )}

        {(showNodes || showRoutes) && (
          <div className="mt-3 flex flex-col gap-1.5 border-t border-white/10 pt-2 text-slate-300">
            {showNodes && (
              <div className="flex items-center gap-2">
                <span
                  aria-hidden
                  className="h-2.5 w-2.5 flex-none rounded-full border border-[#08131f] bg-[#d8f4ff]"
                />
                <span>Place / node</span>
              </div>
            )}
            {showRoutes && (
              <div className="flex items-center gap-2">
                <span
                  aria-hidden
                  className="h-0 w-4 flex-none border-t-2 border-dashed border-[#4bc6d6]"
                />
                <span>Route</span>
              </div>
            )}
          </div>
        )}

        <p className="mt-3 border-t border-white/10 pt-2 text-[10px] leading-4 text-amber-300/90">
          Approximate source-reported extent
        </p>
      </div>
    </div>
  );
}
