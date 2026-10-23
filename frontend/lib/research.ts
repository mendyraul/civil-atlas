import type { CivilizationLayer, SourceRecord } from '../types/atlas';

export function sourceNamespace(source: SourceRecord) {
  return source.sourceNamespace ?? 'manual_seed';
}

export function isCliopatria(layer: CivilizationLayer, sources: SourceRecord[]) {
  return sources.some((source) => layer.sourceRecordIds.includes(source.id) && sourceNamespace(source) === 'cliopatria');
}

export function availableLayers(layers: CivilizationLayer[], sources: SourceRecord[]) {
  return layers.filter((layer) => !isCliopatria(layer, sources) || layer.reviewStatus === 'reviewed');
}

export function boundaryGroup(layer: CivilizationLayer) {
  return layer.variantGroup || layer.civilizationId;
}

export function visibleBoundaryLayers(layers: CivilizationLayer[], choices: Record<string, boolean>) {
  return layers.filter((layer) => {
    if (choices[layer.id] !== undefined) return choices[layer.id];
    if (layer.interpretationKind !== 'boundary_variant') return true;
    const group = layers.filter((item) => item.interpretationKind === 'boundary_variant' && boundaryGroup(item) === boundaryGroup(layer));
    const sourced = group.filter((item) => item.reviewStatus === 'reviewed' && !item.isPlaceholder && !item.geometryPlaceholder);
    const defaults = sourced.length ? sourced : group;
    return defaults.includes(layer) && (!defaults.some((item) => item.isPrimary) || layer.isPrimary);
  });
}
