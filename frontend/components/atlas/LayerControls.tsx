type LayerVisibility = {
  extents: boolean;
  nodes: boolean;
  routes: boolean;
  sources: boolean;
};

type LayerControlsProps = {
  values: LayerVisibility;
  counts: {
    extents: number;
    nodes: number;
    routes: number;
    sources: number;
  };
  onToggle: (layer: keyof LayerVisibility) => void;
};

const layerLabels: Record<keyof LayerVisibility, string> = {
  extents: 'Civilization extents',
  nodes: 'Cities and nodes',
  routes: 'Routes and corridors',
  sources: 'Source evidence markers',
};

export function LayerControls({ values, counts, onToggle }: LayerControlsProps) {
  return (
    <section className="atlas-panel rounded-[28px] p-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="atlas-kicker">Layer controls</p>
          <h2 className="mt-2 text-lg font-semibold text-white">Map stack</h2>
        </div>
        <span className="text-xs uppercase tracking-[0.18em] text-slate-400">Interactive</span>
      </div>

      <div className="mt-4 flex flex-col gap-3">
        {(Object.keys(values) as Array<keyof LayerVisibility>).map((layer) => {
          const enabled = values[layer];
          return (
            <button
              className={`flex items-center justify-between rounded-[20px] border px-4 py-3 text-left transition ${
                enabled
                  ? 'border-cyan-400/50 bg-cyan-400/10 text-white'
                  : 'border-white/8 bg-black/10 text-slate-300 hover:border-white/14 hover:bg-white/[0.04]'
              }`}
              key={layer}
              onClick={() => onToggle(layer)}
              type="button"
            >
              <div>
                <div className="font-medium">{layerLabels[layer]}</div>
                <div className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-400">
                  {enabled ? 'Visible' : 'Hidden'}
                </div>
              </div>
              <div className="rounded-full border border-white/10 px-3 py-1 text-xs text-slate-300">
                {counts[layer]}
              </div>
            </button>
          );
        })}
      </div>

      <div className="mt-4 rounded-[20px] border border-amber-300/18 bg-amber-400/10 px-4 py-3 text-sm leading-6 text-amber-100">
        Approximate source-reported extents stay visibly labeled and should not be read as exact political borders.
      </div>
    </section>
  );
}
