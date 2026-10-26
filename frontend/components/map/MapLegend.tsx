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
  showModernBorders?: boolean;
};

export function MapLegend({
  civilizations,
  showExtents,
  showNodes,
  showRoutes,
  showModernBorders = true,
}: MapLegendProps) {
  const hasContent = civilizations.length > 0 || showNodes || showRoutes;
  if (!hasContent) return null;

  return (
    <div className="pointer-events-none absolute bottom-5 left-5 z-10 max-w-[310px]">
      <div className="pointer-events-auto rounded-[20px] border border-white/12 bg-[#07131f]/80 px-4 py-3 text-xs text-slate-200 shadow-[0_12px_38px_rgba(0,0,0,0.52)] backdrop-blur-xl">
        <p className="text-[10px] uppercase tracking-[0.18em] text-slate-400">Legend</p>

        <div className="mt-3 grid gap-2 border-b border-white/10 pb-3">
          <div className="flex items-center gap-2">
            <span aria-hidden className="h-3 w-5 rounded-[2px] border border-[#942d30] bg-[#942d30]/85" />
            <span>Source-reported territory</span>
          </div>
          <div className="flex items-center gap-2">
            <span aria-hidden className="h-0 w-5 border-t border-dashed border-[#f6c762]" />
            <span>Contested / influence interpretation</span>
          </div>
          <div className="flex items-center gap-2">
            <span aria-hidden className="h-3 w-5 rounded-[2px] border border-white/35 bg-transparent [background-image:repeating-linear-gradient(135deg,transparent_0,transparent_4px,rgba(255,255,255,.35)_4px,rgba(255,255,255,.35)_5px)]" />
            <span>Schematic placeholder, when present</span>
          </div>
          <p className="text-[10px] text-slate-300">Review and confidence are listed in Layer status.</p>
          {showModernBorders && <div className="flex items-center gap-2"><span aria-hidden className="h-3 w-5 rounded-sm bg-[#d8d8ce] p-1"><span className="block border-t border-[#26383c]/50" /></span><span>Present-day borders · reference</span></div>}
        </div>

        {showExtents && civilizations.length > 0 && (
          <ul aria-label="Civilization color legend" className="mt-3 flex max-h-40 flex-col gap-1.5 overflow-y-auto pr-1" tabIndex={0}>
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
          Schematic or source-reported extent · not a precise border
        </p>
      </div>
    </div>
  );
}
