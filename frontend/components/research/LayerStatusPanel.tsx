import type { LayerStatus } from '../../types/atlas';
import { formatYear } from '../../lib/atlas';

export function LayerStatusPanel({ status, compact = false }: { status: LayerStatus; compact?: boolean }) {
  return <details className="layer-status-panel" open={!compact}>
    <summary>Layer status · {status.delivery} · {formatYear(status.year)} · {status.recordCount} records</summary>
    <p className="mt-2 text-xs text-slate-300">Delivery describes loading. Review and confidence describe historical evidence.</p>
    {!status.layers.length && <p className="mt-2 text-sm">No boundary coverage is available for this selection.</p>}
    {status.layers.map((layer) => <article className="mt-3 border-t border-white/10 pt-2 text-xs" key={layer.id}>
      <strong>{layer.interpretationLabel || layer.name}</strong>
      <p className="mt-1">{formatYear(layer.validFromYear)}–{formatYear(layer.validToYear)} · {layer.confidence.replace('_', ' ')} confidence · {layer.reviewStatus.replace('_', ' ')}</p>
      <p className="mt-1">{layer.isPlaceholder || layer.geometryPlaceholder ? 'Schematic placeholder' : 'Source-reported geometry'} · {layer.sourceNote}</p>
      {layer.sourceRecordIds.map((id) => <a className="mt-1 block text-cyan-200 underline" key={id} href={`/sources/${encodeURIComponent(id)}`}>Source & release citation ↗</a>)}
    </article>)}
  </details>;
}
