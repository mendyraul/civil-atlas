import { world117, sourceCatalog } from '../data/demoWorld117';
import { historicalCatalog, historicalCivilizations, historicalSources } from '../data/history/catalog';
import { historyChunks } from '../data/history/loaders';
import { filterWorldByYear } from './atlas';
import type { CivilizationLayer, SourceRecord, WorldPayload } from '../types/atlas';

export const previewCivilizations = historicalCivilizations.map((civilization) => {
  const legacy = world117.civilizations.find((item) => item.id === civilization.id);
  return legacy ? { ...civilization, capital: legacy.capital, shortDescription: legacy.shortDescription } : civilization;
});
export const previewSources: SourceRecord[] = [...new Map([
  ...sourceCatalog, ...historicalSources,
  ...previewCivilizations.flatMap((civilization) => civilization.evidence.map((record) => ({ ...record,
    featureId: civilization.id, featureLabel: civilization.displayName, featureKind: 'civilization' as const }))),
].map((source) => [source.id, source])).values()];

// Imports are cached by the module loader; moving within a century does not
// download geometry again. No interpolation or nearest-year fallback is used.
export async function loadDemoWorld(year: number): Promise<WorldPayload> {
  if (!Number.isInteger(year) || year < historicalCatalog.minYear || year > historicalCatalog.maxYear) throw new Error('Year outside preview coverage');
  const century = Math.floor(year / 100) * 100;
  const loader = historyChunks[String(century) as keyof typeof historyChunks];
  const { default: chunk } = await loader();
  // Generated GeoJSON is validated before review; JSON imports widen tuple and enum types.
  const layers = (chunk.layers as unknown as CivilizationLayer[]).filter((layer) => layer.validFromYear <= year && layer.validToYear >= year);
  const active = new Set(layers.map((layer) => layer.civilizationId));
  const base = filterWorldByYear(world117, year);
  return { ...base, layers, civilizations: previewCivilizations.filter((civilization) => active.has(civilization.id)),
    nodes: base.nodes.filter((node) => !node.civilizationId || active.has(node.civilizationId)),
    routes: base.routes.filter((route) => route.civilizationIds.every((id) => active.has(id))),
  };
}
