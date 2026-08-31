'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import maplibregl, { GeoJSONSource, LngLatBounds, MapMouseEvent } from 'maplibre-gl';
import { NODE_VISIBILITY_ZOOM } from '../../lib/atlas';
import type { AtlasNode, AtlasRoute, Civilization, CivilizationLayer, GeoJSONPosition, TerritorialGeometry } from '../../types/atlas';
import { MapLegend } from './MapLegend';

const OFFLINE_MAP_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {},
  layers: [{ id: 'background', type: 'background', paint: { 'background-color': '#07131f' } }],
};
const MAP_STYLE = process.env.NEXT_PUBLIC_MAP_STYLE_URL || OFFLINE_MAP_STYLE;

type AtlasMapProps = {
  initialCenter: [number, number];
  initialZoom: number;
  civilizations: Civilization[];
  civilizationLayers: CivilizationLayer[];
  evidenceIds: string[];
  nodes: AtlasNode[];
  routes: AtlasRoute[];
  selectedId?: string;
  showEvidence: boolean;
  showExtents: boolean;
  showNodes: boolean;
  showRoutes: boolean;
  onCivilizationSelect: (id: string) => void;
  onNodeSelect: (id: string) => void;
  onRouteSelect: (id: string) => void;
  onZoomChange: (zoom: number) => void;
  onCenterChange: (center: [number, number]) => void;
};

type HoverRef = { source: string; id: string } | null;

const CONFIDENCE_OPACITY = { low: 0.11, medium: 0.17, medium_high: 0.23, high: 0.29 } as const;

function layerFeatureCollection(items: CivilizationLayer[], civilizations: Civilization[]) {
  const civilizationById = new Map(civilizations.map((item) => [item.id, item]));
  return {
    type: 'FeatureCollection' as const,
    features: [...items]
      .sort((a, b) => a.displayOrder - b.displayOrder || Number(b.isPrimary) - Number(a.isPrimary))
      .flatMap((layer) => {
      const civilization = civilizationById.get(layer.civilizationId);
      if (!civilization) return [];
      return [{
      type: 'Feature' as const,
      id: layer.id,
      properties: {
        id: layer.id,
        civilizationId: civilization.id,
        label: layer.interpretationLabel || layer.name,
        color: civilization.color,
        layerType: layer.layerType,
        isPrimary: layer.isPrimary,
        displayOrder: layer.displayOrder,
        confidence: layer.confidence,
        opacity: CONFIDENCE_OPACITY[layer.confidence],
        variantGroup: layer.variantGroup || '',
        isPlaceholder: layer.isPlaceholder ?? Boolean(layer.geometryPlaceholder),
      },
      geometry: layer.geometryJson,
    }];
    }),
  };
}

function geometryPositions(geometry: TerritorialGeometry): GeoJSONPosition[] {
  const polygons = geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates;
  return polygons.flatMap((polygon) => polygon.flatMap((ring) => ring));
}

/** Unwrap longitudes around the first point so dateline features get local bounds. */
function antimeridianBounds(geometries: TerritorialGeometry[]): LngLatBounds | undefined {
  const positions = geometries.flatMap(geometryPositions);
  if (!positions.length) return undefined;
  const anchor = positions[0][0];
  const unwrap = ([longitude, latitude]: GeoJSONPosition): GeoJSONPosition => {
    let adjusted = longitude;
    while (adjusted - anchor > 180) adjusted -= 360;
    while (adjusted - anchor < -180) adjusted += 360;
    return [adjusted, latitude];
  };
  const first = unwrap(positions[0]);
  return positions.slice(1).reduce((bounds, position) => bounds.extend(unwrap(position)), new LngLatBounds(first, first));
}

function nodeFeatureCollection(items: AtlasNode[]) {
  return {
    type: 'FeatureCollection' as const,
    features: items.map((node) => ({
      type: 'Feature' as const,
      id: node.id,
      properties: {
        id: node.id,
        label: node.label,
        nodeKind: node.nodeKind,
      },
      geometry: {
        type: 'Point' as const,
        coordinates: node.coordinates,
      },
    })),
  };
}

function routeFeatureCollection(items: AtlasRoute[]) {
  return {
    type: 'FeatureCollection' as const,
    features: items.map((route) => ({
      type: 'Feature' as const,
      id: route.id,
      properties: {
        id: route.id,
        label: route.label,
        routeKind: route.routeKind,
      },
      geometry: {
        type: 'LineString' as const,
        coordinates: route.path,
      },
    })),
  };
}

// A7: selected extent stays prominent while others recede; no selection = uniform.
function fillOpacityExpression(selectedId?: string): maplibregl.ExpressionSpecification {
  const target = selectedId ?? '';
  return [
    'case',
    ['boolean', ['feature-state', 'hover'], false],
    0.34,
    ['==', ['get', 'civilizationId'], target],
    ['min', 0.38, ['+', ['get', 'opacity'], 0.08]],
    target.length > 0 ? ['*', ['get', 'opacity'], 0.48] : ['get', 'opacity'],
  ];
}

function lineWidthExpression(selectedId?: string): maplibregl.ExpressionSpecification {
  return [
    'interpolate',
    ['linear'],
    ['zoom'],
    1,
    ['case', ['==', ['get', 'civilizationId'], selectedId ?? ''], 2.4, ['case', ['get', 'isPrimary'], 1.15, 0.7]],
    5,
    ['case', ['==', ['get', 'civilizationId'], selectedId ?? ''], 3.6, ['case', ['get', 'isPrimary'], 1.8, 1.1]],
  ];
}

function lineOpacityExpression(selectedId?: string): maplibregl.ExpressionSpecification {
  const target = selectedId ?? '';
  return [
    'case',
    ['boolean', ['feature-state', 'hover'], false],
    0.72,
    ['==', ['get', 'civilizationId'], target],
    0.64,
    target.length > 0 ? 0.12 : 0.28,
  ];
}

type MapState = {
  evidenceIds: string[];
  nodes: ReturnType<typeof nodeFeatureCollection>;
  nodeItems: AtlasNode[];
  polygons: ReturnType<typeof layerFeatureCollection>;
  routes: ReturnType<typeof routeFeatureCollection>;
  selectedId?: string;
  showEvidence: boolean;
  showExtents: boolean;
  showNodes: boolean;
  showRoutes: boolean;
};

const requiredLayerIds = [
  'civilizations-outline-glow',
  'civilizations-fill',
  'civilizations-line',
  'nodes-halo',
  'nodes-circle',
  'nodes-label',
  'routes-glow',
  'routes-line',
  'selected-evidence-glow',
] as const;

function applyCurrentMapState(map: maplibregl.Map, state: MapState) {
  (map.getSource('civilizations') as GeoJSONSource | undefined)?.setData(state.polygons);
  (map.getSource('nodes') as GeoJSONSource | undefined)?.setData(state.nodes);
  (map.getSource('routes') as GeoJSONSource | undefined)?.setData(state.routes);

  if (map.getLayer('civilizations-line')) {
    map.setPaintProperty('civilizations-line', 'line-width', lineWidthExpression(state.selectedId));
    map.setPaintProperty(
      'civilizations-line',
      'line-opacity',
      lineOpacityExpression(state.selectedId),
    );
    map.setPaintProperty(
      'civilizations-fill',
      'fill-opacity',
      fillOpacityExpression(state.selectedId),
    );
    map.setPaintProperty('civilizations-outline-glow', 'line-width', [
      'interpolate', ['linear'], ['zoom'], 1,
      ['case', ['==', ['get', 'civilizationId'], state.selectedId ?? ''], 12, 7], 5,
      ['case', ['==', ['get', 'civilizationId'], state.selectedId ?? ''], 18, 10],
    ]);
    map.setPaintProperty('civilizations-outline-glow', 'line-opacity', [
      'case', ['==', ['get', 'civilizationId'], state.selectedId ?? ''], 0.18, 0.1,
    ]);
  }

  const evidenceIds = new Set(state.evidenceIds);
  (map.getSource('selected-evidence') as GeoJSONSource | undefined)?.setData({
    type: 'FeatureCollection',
    features: state.nodeItems
      .filter((node) => node.evidence.some((record) => evidenceIds.has(record.id)))
      .map((node) => ({
        type: 'Feature' as const,
        properties: { id: node.id },
        geometry: { type: 'Point' as const, coordinates: node.coordinates },
      })),
  });

  const visibility = (shown: boolean) => (shown ? 'visible' : 'none');
    (['civilizations-outline-glow', 'civilizations-fill', 'civilizations-line'] as const)
      .forEach((id) => {
      if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', visibility(state.showExtents));
    });
  if (map.getLayer('civilizations-placeholder-hatch')) {
    map.setLayoutProperty('civilizations-placeholder-hatch', 'visibility', visibility(state.showExtents));
  }
  (['nodes-halo', 'nodes-circle', 'nodes-label'] as const)
    .forEach((id) => {
      if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', visibility(state.showNodes));
    });
  (['routes-glow', 'routes-line'] as const)
    .forEach((id) => {
      if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', visibility(state.showRoutes));
    });
  if (map.getLayer('selected-evidence-glow')) {
    map.setLayoutProperty('selected-evidence-glow', 'visibility', visibility(state.showEvidence));
  }
}

export function AtlasMap({
  initialCenter,
  initialZoom,
  civilizations,
  civilizationLayers,
  evidenceIds,
  nodes,
  routes,
  selectedId,
  showEvidence,
  showExtents,
  showNodes,
  showRoutes,
  onCivilizationSelect,
  onNodeSelect,
  onRouteSelect,
  onZoomChange,
  onCenterChange,
}: AtlasMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const hoverRef = useRef<HoverRef>(null);
  const popupRef = useRef<maplibregl.Popup | null>(null);
  const lastFlownRef = useRef<string | undefined>(undefined);
  const [mapStatus, setMapStatus] = useState<'loading' | 'ready' | 'failed'>('loading');
  const [mapError, setMapError] = useState('');
  const [retryKey, setRetryKey] = useState(0);
  const initialViewRef = useRef({ center: initialCenter, zoom: initialZoom });

  // Keep the latest callbacks in a ref so the map init effect can run exactly once.
  const handlersRef = useRef({
    onCivilizationSelect,
    onNodeSelect,
    onRouteSelect,
    onZoomChange,
    onCenterChange,
  });
  handlersRef.current = {
    onCivilizationSelect,
    onNodeSelect,
    onRouteSelect,
    onZoomChange,
    onCenterChange,
  };

  const polygonData = useMemo(
    () => layerFeatureCollection(civilizationLayers, civilizations),
    [civilizationLayers, civilizations],
  );
  const previousPolygonDataRef = useRef(polygonData);
  const pointData = useMemo(() => nodeFeatureCollection(nodes), [nodes]);
  const routeData = useMemo(() => routeFeatureCollection(routes), [routes]);
  const currentMapStateRef = useRef<MapState>({
    evidenceIds,
    nodes: pointData,
    nodeItems: nodes,
    polygons: polygonData,
    routes: routeData,
    selectedId,
    showEvidence,
    showExtents,
    showNodes,
    showRoutes,
  });
  currentMapStateRef.current = {
    evidenceIds,
    nodes: pointData,
    nodeItems: nodes,
    polygons: polygonData,
    routes: routeData,
    selectedId,
    showEvidence,
    showExtents,
    showNodes,
    showRoutes,
  };

  // A1 + init: create the map once and register interaction handlers.
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    setMapStatus('loading');
    setMapError('');

    let map: maplibregl.Map;
    try {
      map = new maplibregl.Map({
        container: containerRef.current,
        style: MAP_STYLE,
        center: initialViewRef.current.center,
        zoom: initialViewRef.current.zoom,
        attributionControl: { compact: true },
      });
    } catch (error) {
      setMapStatus('failed');
      setMapError(error instanceof Error ? error.message : 'The map could not be created.');
      return;
    }

    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right');

    const popup = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
      offset: 12,
      className: 'atlas-hover-popup',
    });
    popupRef.current = popup;

    const handleMapError = (event?: maplibregl.ErrorEvent) => {
      setMapStatus('failed');
      setMapError(event?.error?.message || 'The basemap could not be loaded.');
    };
    const handleStyleData = () => {
      if (map.isStyleLoaded()) setMapStatus((status) => status === 'failed' ? status : 'ready');
      if (requiredLayerIds.every((id) => Boolean(map.getLayer(id)))) {
        applyCurrentMapState(map, currentMapStateRef.current);
      }
    };
    map.on('error', handleMapError);
    map.on('styledata', handleStyleData);

    const clearHover = () => {
      if (hoverRef.current) {
        map.setFeatureState(hoverRef.current, { hover: false });
        hoverRef.current = null;
      }
      popup.remove();
      map.getCanvas().style.cursor = '';
    };

    const handleLoad = () => {
      setMapStatus('ready');
      setMapError('');
      // A1: globe projection + atmosphere.
      map.setProjection({ type: 'globe' });
      map.setSky({
        'sky-color': '#0a1420',
        'sky-horizon-blend': 0.5,
        'horizon-color': '#0d2233',
        'horizon-fog-blend': 0.6,
        'fog-color': '#06101a',
        'fog-ground-blend': 0.2,
        'atmosphere-blend': ['interpolate', ['linear'], ['zoom'], 0, 0.85, 6, 0.2],
      });

      const emptyData = { type: 'FeatureCollection' as const, features: [] };
      map.addSource('civilizations', { type: 'geojson', data: emptyData, promoteId: 'id' });
      map.addSource('nodes', { type: 'geojson', data: emptyData, promoteId: 'id' });
      map.addSource('routes', { type: 'geojson', data: emptyData, promoteId: 'id' });

      // A6: soft glow underlayer beneath the crisp route lines.
      map.addLayer({
        id: 'routes-glow',
        type: 'line',
        source: 'routes',
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: {
          'line-color': '#4bc6d6',
          'line-width': ['interpolate', ['linear'], ['zoom'], 1, 4, 4, 8, 7, 12],
          'line-opacity': 0.18,
          'line-blur': 6,
        },
      });

      map.addLayer({
        id: 'routes-line',
        type: 'line',
        source: 'routes',
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: {
          'line-color': [
            'case',
            ['boolean', ['feature-state', 'hover'], false],
            '#a5f0fb',
            '#4bc6d6',
          ],
          'line-width': ['interpolate', ['linear'], ['zoom'], 1, 1, 4, 2, 7, 3],
          'line-opacity': 0.82,
          'line-dasharray': [2, 1.4],
        },
      });

      map.addLayer({
        id: 'civilizations-outline-glow',
        type: 'line',
        source: 'civilizations',
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: {
          'line-color': ['get', 'color'],
          'line-width': [
            'interpolate',
            ['linear'],
            ['zoom'],
            1,
            ['case', ['==', ['get', 'civilizationId'], currentMapStateRef.current.selectedId ?? ''], 12, 7],
            5,
            ['case', ['==', ['get', 'civilizationId'], currentMapStateRef.current.selectedId ?? ''], 18, 10],
          ],
          'line-opacity': [
            'case',
            ['==', ['get', 'civilizationId'], currentMapStateRef.current.selectedId ?? ''],
            0.18,
            0.1,
          ],
          'line-blur': 7,
        },
      });

      map.addLayer({
        id: 'civilizations-fill',
        type: 'fill',
        source: 'civilizations',
        paint: {
          'fill-color': ['get', 'color'],
          'fill-opacity': fillOpacityExpression(currentMapStateRef.current.selectedId),
          // A4: cross-fade extents when the active year (and thus features) changes.
          'fill-opacity-transition': { duration: 450, delay: 0 },
        },
      });

      // Schematic geometry gets an unmistakable diagonal hatch overlay. It is
      // intentionally independent of confidence and interpretation styling.
      const patternCanvas = document.createElement('canvas');
      patternCanvas.width = 16;
      patternCanvas.height = 16;
      const context = patternCanvas.getContext('2d');
      if (context) {
        context.strokeStyle = 'rgba(255,255,255,0.72)';
        context.lineWidth = 2;
        context.beginPath();
        context.moveTo(-4, 16);
        context.lineTo(16, -4);
        context.moveTo(4, 20);
        context.lineTo(20, 4);
        context.stroke();
        map.addImage('schematic-hatch', context.getImageData(0, 0, 16, 16));
        map.addLayer({
          id: 'civilizations-placeholder-hatch',
          type: 'fill',
          source: 'civilizations',
          filter: ['==', ['get', 'isPlaceholder'], true],
          paint: { 'fill-pattern': 'schematic-hatch', 'fill-opacity': 0.48 },
        });
      }

      map.addLayer({
        id: 'civilizations-line',
        type: 'line',
        source: 'civilizations',
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: {
          'line-color': ['get', 'color'],
          'line-width': lineWidthExpression(currentMapStateRef.current.selectedId),
          'line-opacity': lineOpacityExpression(currentMapStateRef.current.selectedId),
          'line-blur': 0.6,
          'line-dasharray': [
            'match', ['get', 'layerType'],
            ['influence_zone', 'cultural_extent', 'trade_network'], ['literal', [3, 2]],
            ['contested_zone', 'source_reported_extent'], ['literal', [1.2, 1.4]],
            ['literal', [1, 1]],
          ],
          'line-opacity-transition': { duration: 450, delay: 0 },
        },
      });

      // A6: soft halo beneath each node.
      map.addLayer({
        id: 'nodes-halo',
        type: 'circle',
        source: 'nodes',
        minzoom: NODE_VISIBILITY_ZOOM,
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['zoom'], NODE_VISIBILITY_ZOOM, 9, 7, 18],
          'circle-color': '#7fe3f5',
          'circle-opacity': 0.16,
          'circle-blur': 0.8,
        },
      });

      map.addLayer({
        id: 'nodes-circle',
        type: 'circle',
        source: 'nodes',
        minzoom: NODE_VISIBILITY_ZOOM,
        paint: {
          'circle-radius': [
            'interpolate',
            ['linear'],
            ['zoom'],
            NODE_VISIBILITY_ZOOM,
            ['case', ['boolean', ['feature-state', 'hover'], false], 6, 4],
            7,
            ['case', ['boolean', ['feature-state', 'hover'], false], 10, 8],
          ],
          'circle-color': ['case', ['boolean', ['feature-state', 'hover'], false], '#ffffff', '#d8f4ff'],
          'circle-stroke-color': '#08131f',
          'circle-stroke-width': 1.5,
        },
      });

      map.addLayer({
        id: 'nodes-label',
        type: 'symbol',
        source: 'nodes',
        minzoom: NODE_VISIBILITY_ZOOM + 0.2,
        layout: {
          'text-field': ['get', 'label'],
          'text-font': ['Noto Sans Regular'],
          'text-size': 12,
          'text-offset': [0, 1.2],
        },
        paint: {
          'text-color': '#f3f8ff',
          'text-halo-color': '#09131f',
          'text-halo-width': 1.1,
        },
      });

      map.addSource('selected-evidence', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      });

      map.addLayer({
        id: 'selected-evidence-glow',
        type: 'circle',
        source: 'selected-evidence',
        minzoom: NODE_VISIBILITY_ZOOM,
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['zoom'], NODE_VISIBILITY_ZOOM, 8, 7, 15],
          'circle-color': '#f6c762',
          'circle-opacity': 0.16,
        },
      });

      const asId = (event: MapMouseEvent, layerId: string) =>
        map.queryRenderedFeatures(event.point, { layers: [layerId] })[0]?.properties?.id;

      map.on('click', 'civilizations-fill', (event) => {
        const id = map.queryRenderedFeatures(event.point, { layers: ['civilizations-fill'] })[0]?.properties?.civilizationId;
        if (typeof id === 'string') handlersRef.current.onCivilizationSelect(id);
      });

      map.on('click', 'nodes-circle', (event) => {
        const id = asId(event, 'nodes-circle');
        if (typeof id === 'string') handlersRef.current.onNodeSelect(id);
      });

      map.on('click', 'routes-line', (event) => {
        const id = asId(event, 'routes-line');
        if (typeof id === 'string') handlersRef.current.onRouteSelect(id);
      });

      // A3: hover highlight + cursor + tooltip.
      const hoverLayers = ['civilizations-fill', 'nodes-circle', 'routes-line'] as const;
      const sourceForLayer: Record<string, string> = {
        'civilizations-fill': 'civilizations',
        'nodes-circle': 'nodes',
        'routes-line': 'routes',
      };

      hoverLayers.forEach((layerId) => {
        map.on('mousemove', layerId, (event) => {
          const feature = event.features?.[0];
          const id = layerId === 'civilizations-fill'
            ? feature?.properties?.civilizationId
            : feature?.properties?.id;
          if (typeof id !== 'string') return;

          const source = sourceForLayer[layerId];
          if (hoverRef.current && (hoverRef.current.id !== id || hoverRef.current.source !== source)) {
            map.setFeatureState(hoverRef.current, { hover: false });
          }
          const featureStateId = feature?.properties?.id;
          if (typeof featureStateId !== 'string') return;
          hoverRef.current = { source, id: featureStateId };
          map.setFeatureState(hoverRef.current, { hover: true });
          map.getCanvas().style.cursor = 'pointer';

          const label = feature?.properties?.label;
          if (typeof label === 'string') {
            popup
              .setLngLat(event.lngLat)
              .setHTML(`<span class="atlas-hover-popup__label">${label}</span>`)
              .addTo(map);
          }
        });

        map.on('mouseleave', layerId, clearHover);
      });

      map.on('zoom', () => handlersRef.current.onZoomChange(map.getZoom()));
      map.on('moveend', () => { const center = map.getCenter(); handlersRef.current.onCenterChange([center.lng, center.lat]); });
      handlersRef.current.onZoomChange(map.getZoom());
      applyCurrentMapState(map, currentMapStateRef.current);
    };

    map.on('load', handleLoad);
    map.on('styledata', handleStyleData);

    return () => {
      popup.remove();
      popupRef.current = null;
      map.off('load', handleLoad);
      map.off('styledata', handleStyleData);
      map.remove();
      mapRef.current = null;
      hoverRef.current = null;
    };
  }, [retryKey]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    applyCurrentMapState(map, currentMapStateRef.current);
  }, [
    polygonData,
    pointData,
    routeData,
    evidenceIds,
    nodes,
    selectedId,
    showEvidence,
    showExtents,
    showNodes,
    showRoutes,
  ]);

  // A4: GeoJSON replacement is a hard data swap in MapLibre. Briefly fading
  // the fill out makes a year/filter change feel intentional while keeping
  // the outline and labels available during the transition.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded() || previousPolygonDataRef.current === polygonData) return;
    previousPolygonDataRef.current = polygonData;

    map.setPaintProperty('civilizations-fill', 'fill-opacity', 0);
    const frame = window.requestAnimationFrame(() => {
      if (mapRef.current === map && map.isStyleLoaded()) {
        applyCurrentMapState(map, currentMapStateRef.current);
      }
    });

    return () => window.cancelAnimationFrame(frame);
  }, [polygonData]);

  // A2: fly the camera to frame the newly selected feature.
  useEffect(() => {
    const map = mapRef.current;
    if (!selectedId) {
      lastFlownRef.current = undefined;
      return;
    }
    if (!map || !map.isStyleLoaded()) return;
    if (lastFlownRef.current === selectedId) return;

    const civilization = civilizations.find((item) => item.id === selectedId);
    const node = nodes.find((item) => item.id === selectedId);
    const route = routes.find((item) => item.id === selectedId);

    if (civilization) {
      const bounds = antimeridianBounds(
        civilizationLayers
          .filter((layer) => layer.civilizationId === civilization.id)
          .map((layer) => layer.geometryJson),
      );
      if (bounds) map.fitBounds(bounds, { padding: 96, maxZoom: 5, duration: 900 });
    } else if (route && route.path.length > 0) {
      const bounds = route.path.reduce(
        (acc, coordinate) => acc.extend(coordinate),
        new LngLatBounds(route.path[0], route.path[0]),
      );
      map.fitBounds(bounds, { padding: 120, maxZoom: 5.5, duration: 900 });
    } else if (node) {
      map.flyTo({
        center: node.coordinates,
        zoom: Math.max(map.getZoom(), NODE_VISIBILITY_ZOOM + 1.2),
        duration: 900,
      });
    }

    lastFlownRef.current = selectedId;
  }, [selectedId, civilizations, civilizationLayers, nodes, routes]);

  return (
    <div className="relative h-[68vh] min-h-[560px] w-full" role="group" aria-label="Interactive historical atlas map. Use Tab to reach map controls and arrow keys to pan.">
      <div
        aria-label="Interactive historical atlas map. Use Tab to reach map controls and arrow keys to pan."
        className="h-full w-full"
        ref={containerRef}
        role="application"
        tabIndex={0}
      />
      {mapStatus !== 'ready' && (
        <div
          aria-live="assertive"
          className="absolute inset-0 z-20 flex items-center justify-center bg-[#06101a]/95 p-6 text-center"
          role={mapStatus === 'failed' ? 'alert' : 'status'}
        >
          <div className="max-w-md rounded-2xl border border-white/10 bg-[#0b1724] p-6 shadow-2xl">
            <p className="atlas-kicker">{mapStatus === 'failed' ? 'Map unavailable' : 'Loading map'}</p>
            <p className="mt-3 text-sm text-slate-300">
              {mapStatus === 'failed'
                ? mapError || 'The basemap could not be loaded.'
                : 'Loading basemap, labels, and atlas layers…'}
            </p>
            {mapStatus === 'failed' && (
              <button
                className="mt-5 rounded-full border border-cyan-300/40 bg-cyan-300/10 px-5 py-2 text-sm font-semibold text-cyan-100 hover:bg-cyan-300/20 focus:outline-none focus:ring-2 focus:ring-cyan-200"
                onClick={() => setRetryKey((key) => key + 1)}
                type="button"
              >
                Retry map
              </button>
            )}
          </div>
        </div>
      )}
      <div className="sr-only" aria-label="Map features">
        {[...civilizations, ...nodes, ...routes].map((feature) => (
          <button key={feature.id} onClick={() => feature.kind === 'civilization' ? onCivilizationSelect(feature.id) : feature.kind === 'node' ? onNodeSelect(feature.id) : onRouteSelect(feature.id)} type="button">
            Open {feature.label}
          </button>
        ))}
      </div>
      <MapLegend
        civilizations={civilizations.map((civilization) => ({
          id: civilization.id,
          label: civilization.label,
          color: civilization.color,
        }))}
        showExtents={showExtents}
        showNodes={showNodes}
        showRoutes={showRoutes}
      />
    </div>
  );
}
