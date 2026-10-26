import type { Civilization, CivilizationLayer, GeoJSONPosition, TerritorialGeometry } from '../types/atlas';

// One interior anchor on the largest land component prevents a label on every
// island and vector tile. This only positions text; source borders stay untouched.
function labelPosition(geometry: TerritorialGeometry): GeoJSONPosition {
  const polygons = geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates;
  const area = (ring: GeoJSONPosition[]) => Math.abs(ring.reduce((sum, [x, y], i) => {
    const [nextX, nextY] = ring[(i + 1) % ring.length];
    return sum + x * nextY - nextX * y;
  }, 0));
  const rings = [...polygons].sort((a, b) => area(b[0]) - area(a[0]))[0];
  const latitudes = rings[0].map((point) => point[1]);
  const south = Math.min(...latitudes), north = Math.max(...latitudes);
  let anchor = rings[0][0], widest = 0;
  for (const fraction of [0.5, 0.35, 0.65, 0.2, 0.8]) {
    const y = south + (north - south) * fraction;
    const crossings = rings.flatMap((ring) => ring.flatMap(([ax, ay], i) => {
      const [bx, by] = ring[(i + 1) % ring.length];
      return (ay > y) !== (by > y) ? [ax + (y - ay) * (bx - ax) / (by - ay)] : [];
    })).sort((a, b) => a - b);
    for (let i = 0; i + 1 < crossings.length; i += 2) {
      const width = crossings[i + 1] - crossings[i];
      if (width > widest) { widest = width; anchor = [(crossings[i] + crossings[i + 1]) / 2, y]; }
    }
  }
  return anchor;
}

export function civilizationLabels(layers: CivilizationLayer[], civilizations: Civilization[]) {
  return {
    type: 'FeatureCollection' as const,
    features: civilizations.flatMap((civilization) => {
      const candidates = layers.filter((layer) => layer.civilizationId === civilization.id);
      const layer = candidates.find((candidate) => candidate.isPrimary) ?? candidates[0];
      return layer ? [{ type: 'Feature' as const, id: civilization.id,
        properties: { civilizationId: civilization.id, civilizationLabel: civilization.displayName },
        geometry: { type: 'Point' as const, coordinates: labelPosition(layer.geometryJson) },
      }] : [];
    }),
  };
}
