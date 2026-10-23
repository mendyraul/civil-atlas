'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import { GeoJSONSource, LngLatBounds, MapMouseEvent } from 'maplibre-gl';
import { NODE_VISIBILITY_ZOOM } from '../../lib/atlas';
import type { MapAnnotation, GeoJSONPosition as DrawingPosition, AtlasCamera, AtlasNode, AtlasRoute, Civilization, CivilizationLayer, GeoJSONPosition, TerritorialGeometry } from '../../types/atlas';
import { MapLegend } from './MapLegend';

// Next.js emits a same-origin, content-hashed worker asset for both bundlers.
maplibregl.setWorkerUrl(new URL('maplibre-gl/dist/maplibre-gl-worker.mjs', import.meta.url).toString());

const MAP_STYLE = process.env.NEXT_PUBLIC_MAP_STYLE_URL || '/map-styles/minimal.json';

type AtlasMapProps = {
  annotations?: MapAnnotation[];
  imageOverlays?: Array<{ id: string; url: string; bounds: [number, number, number, number] }>;
  drawMode?: 'Point' | 'LineString' | 'Polygon' | 'Rectangle' | null;
  onDrawPoint?: (point: DrawingPosition) => void;
  onFinishDraw?: () => void;
  onBoundsChange?: (bounds: [number, number, number, number]) => void;
  cameraCommand?: AtlasCamera;
  onCameraChange?: (camera: AtlasCamera) => void;
  reducedMotion?: boolean;
  cliopatriaVisible?: boolean;
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

const CONFIDENCE_OPACITY = { low: 0.14, medium: 0.2, medium_high: 0.28, high: 0.35 } as const;

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
        civilizationLabel: civilization.displayName,
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
  'civilizations-label',
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
    (['civilizations-outline-glow', 'civilizations-fill', 'civilizations-line', 'civilizations-label'] as const)
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
  (['selected-evidence-glow', 'selected-evidence-core'] as const).forEach((id) => {
    if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', visibility(state.showEvidence));
  });
}

const EMPTY_ANNOTATIONS: MapAnnotation[] = [];
const EMPTY_IMAGES: NonNullable<AtlasMapProps['imageOverlays']> = [];

export function AtlasMap({
  annotations = EMPTY_ANNOTATIONS, imageOverlays = EMPTY_IMAGES, drawMode = null, onDrawPoint, onFinishDraw, onBoundsChange,
  cameraCommand,
  onCameraChange,
  reducedMotion = false,
  cliopatriaVisible = false,
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
  const drawRef = useRef({ drawMode, onDrawPoint, onBoundsChange });
  drawRef.current = { drawMode, onDrawPoint, onBoundsChange };
  const layersReady = useRef(false);
  const overlayIds = useRef<string[]>([]);
  const commandRef = useRef(cameraCommand);
  commandRef.current = cameraCommand;
  const cameraChangeRef = useRef(onCameraChange);
  cameraChangeRef.current = onCameraChange;
  const [legendOpen, setLegendOpen] = useState(false);
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
        attributionControl: false,
      });
    } catch (error) {
      setMapStatus('failed');
      setMapError(error instanceof Error ? error.message : 'The map could not be created.');
      return;
    }

    mapRef.current = map;
    const resize = new ResizeObserver(() => map.resize());
    resize.observe(containerRef.current);
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
      if (layersReady.current && map.isStyleLoaded()) setMapStatus((status) => status === 'failed' ? status : 'ready');
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
          'line-opacity': 0.25,
          'line-blur': 5,
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
          'line-opacity': 0.78,
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
          paint: { 'fill-pattern': 'schematic-hatch', 'fill-opacity': 0.3 },
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

      map.addLayer({
        id: 'civilizations-label',
        type: 'symbol',
        source: 'civilizations',
        filter: ['==', ['get', 'isPrimary'], true],
        minzoom: 1.3,
        layout: {
          'text-field': ['get', 'civilizationLabel'],
          'text-font': ['Noto Sans Regular'],
          'text-size': ['interpolate', ['linear'], ['zoom'], 1.3, 10, 4, 15, 6, 18],
          'text-letter-spacing': 0.08,
          'text-max-width': 9,
          'text-allow-overlap': true,
          'text-ignore-placement': true,
        },
        paint: {
          'text-color': '#f3e9d2',
          'text-opacity': [
            'case',
            ['==', ['get', 'civilizationId'], currentMapStateRef.current.selectedId ?? ''],
            0.98,
            0.7,
          ],
          'text-halo-color': '#08131f',
          'text-halo-width': 1.8,
          'text-halo-blur': 0.3,
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

      map.addLayer({
        id: 'selected-evidence-core',
        type: 'circle',
        source: 'selected-evidence',
        minzoom: NODE_VISIBILITY_ZOOM,
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['zoom'], NODE_VISIBILITY_ZOOM, 2.5, 7, 4],
          'circle-color': '#f6c762',
          'circle-stroke-color': '#fff2c7',
          'circle-stroke-width': 1,
          'circle-opacity': 0.92,
        },
      });

      const asId = (event: MapMouseEvent, layerId: string) =>
        map.queryRenderedFeatures(event.point, { layers: [layerId] })[0]?.properties?.id;

      map.on('click', (event) => { if (drawRef.current.drawMode) drawRef.current.onDrawPoint?.([event.lngLat.lng, event.lngLat.lat]); });
      map.on('click', 'civilizations-fill', (event) => {
        if (drawRef.current.drawMode) return;
        const id = map.queryRenderedFeatures(event.point, { layers: ['civilizations-fill'] })[0]?.properties?.civilizationId;
        if (typeof id === 'string') handlersRef.current.onCivilizationSelect(id);
      });

      map.on('click', 'nodes-circle', (event) => {
        if (drawRef.current.drawMode) return;
        const id = asId(event, 'nodes-circle');
        if (typeof id === 'string') handlersRef.current.onNodeSelect(id);
      });

      map.on('click', 'routes-line', (event) => {
        if (drawRef.current.drawMode) return;
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
              .setText(label)
              .addTo(map);
          }
        });

        map.on('mouseleave', layerId, clearHover);
      });

      map.on('zoom', () => handlersRef.current.onZoomChange(map.getZoom()));
      map.on('moveend', () => { const bounds = map.getBounds(); drawRef.current.onBoundsChange?.([bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()]); const center = map.getCenter(); handlersRef.current.onCenterChange([center.lng, center.lat]); cameraChangeRef.current?.({ center: [center.lng, center.lat], zoom: map.getZoom(), bearing: map.getBearing(), pitch: map.getPitch() }); });
      handlersRef.current.onZoomChange(map.getZoom());
      map.addSource('research-annotations', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
      map.addLayer({ id: 'research-annotation-fill', type: 'fill', source: 'research-annotations', filter: ['==', ['geometry-type'], 'Polygon'], paint: { 'fill-color': '#f2d39a', 'fill-opacity': 0.12 } });
      map.addLayer({ id: 'research-annotation-line', type: 'line', source: 'research-annotations', filter: ['!=', ['geometry-type'], 'Point'], paint: { 'line-color': '#f2d39a', 'line-width': 3, 'line-dasharray': [2, 2] } });
      map.addLayer({ id: 'research-annotation-point', type: 'circle', source: 'research-annotations', filter: ['==', ['geometry-type'], 'Point'], paint: { 'circle-radius': 6, 'circle-color': '#f2d39a', 'circle-stroke-color': '#091827', 'circle-stroke-width': 2 } });
      map.on('click', 'research-annotation-point', (event) => { const feature = event.features?.[0]; if (drawRef.current.drawMode || !feature) return; popup.setLngLat(event.lngLat).setText(String(feature.properties?.title || 'Annotation')).addTo(map); });
      layersReady.current = true;
      applyCurrentMapState(map, currentMapStateRef.current);
      setMapStatus('ready');
      if (commandRef.current) map.jumpTo({ ...commandRef.current });
      const bounds = map.getBounds(); drawRef.current.onBoundsChange?.([bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()]);
    };

    map.on('load', handleLoad);

    return () => {
      layersReady.current = false;
      resize.disconnect();
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
    if (!map || !layersReady.current) return;
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
    mapStatus,
  ]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || mapStatus !== 'ready' || !cameraCommand) return;
    const current = map.getCenter();
    if (Math.abs(current.lng - cameraCommand.center[0]) < 0.0001 && Math.abs(current.lat - cameraCommand.center[1]) < 0.0001 && Math.abs(map.getZoom() - cameraCommand.zoom) < 0.001 && Math.abs(map.getBearing() - (cameraCommand.bearing ?? 0)) < 0.01 && Math.abs(map.getPitch() - (cameraCommand.pitch ?? 0)) < 0.01) return;
    map.stop();
    map.flyTo({ ...cameraCommand, duration: reducedMotion ? 0 : 1100 });
  }, [cameraCommand, mapStatus, reducedMotion]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || mapStatus !== 'ready') return;
    const control = new maplibregl.AttributionControl({ compact: true, customAttribution: cliopatriaVisible ? 'Borders: Cliopatria (Seshat), <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>' : undefined });
    map.addControl(control, 'bottom-right');
    return () => { if (mapRef.current === map) map.removeControl(control); };
  }, [cliopatriaVisible, mapStatus]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || mapStatus !== 'ready') return;
    const source = map.getSource('research-annotations') as GeoJSONSource | undefined;
    source?.setData({ type: 'FeatureCollection', features: annotations.flatMap((annotation) => {
      const geometry = annotation.geometry ?? civilizationLayers.find((l) => l.id === annotation.boundaryLayerId)?.geometryJson;
      return geometry ? [{ type: 'Feature' as const, id: annotation.id, properties: { title: annotation.title }, geometry }] : [];
    }) });
  }, [annotations, civilizationLayers, mapStatus]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || mapStatus !== 'ready') return;
    for (const id of overlayIds.current) { if (map.getLayer(id)) map.removeLayer(id); if (map.getSource(id)) map.removeSource(id); }
    overlayIds.current = [];
    for (const image of imageOverlays) {
      const id = `episode-image-${image.id}`, [w, south, east, n] = image.bounds;
      map.addSource(id, { type: 'image', url: image.url, coordinates: [[w, n], [east, n], [east, south], [w, south]] });
      map.addLayer({ id, type: 'raster', source: id, paint: { 'raster-opacity': 0.65 } }, 'civilizations-fill'); overlayIds.current.push(id);
    }
  }, [imageOverlays, mapStatus]);

  // A2: fly the camera to frame the newly selected feature.
  useEffect(() => {
    const map = mapRef.current;
    if (!selectedId) {
      lastFlownRef.current = undefined;
      return;
    }
    if (!map || !layersReady.current || cameraCommand) return;
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
      if (bounds) map.fitBounds(bounds, { padding: 96, maxZoom: 5, duration: reducedMotion ? 0 : 900 });
    } else if (route && route.path.length > 0) {
      const bounds = route.path.reduce(
        (acc, coordinate) => acc.extend(coordinate),
        new LngLatBounds(route.path[0], route.path[0]),
      );
      map.fitBounds(bounds, { padding: 120, maxZoom: 5.5, duration: reducedMotion ? 0 : 900 });
    } else if (node) {
      map.flyTo({
        center: node.coordinates,
        zoom: Math.max(map.getZoom(), NODE_VISIBILITY_ZOOM + 1.2),
        duration: reducedMotion ? 0 : 900,
      });
    }

    lastFlownRef.current = selectedId;
  }, [selectedId, civilizations, civilizationLayers, nodes, routes, cameraCommand, reducedMotion, mapStatus]);

  return (
    <div className="atlas-globe relative h-full min-h-[420px] w-full" role="group" aria-label="Interactive historical atlas map. Use Tab to reach map controls and arrow keys to pan.">
      <div
        aria-label="Interactive historical atlas map. Use Tab to reach map controls and arrow keys to pan."
        className="h-full w-full"
        ref={containerRef}
        role="application"
        tabIndex={0}
      />
      <div aria-hidden className="atlas-map-atmosphere" />
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
      <div className="sr-only" role="group" aria-label="Map features">
        {[...civilizations, ...nodes, ...routes].map((feature) => (
          <button key={feature.id} onClick={() => feature.kind === 'civilization' ? onCivilizationSelect(feature.id) : feature.kind === 'node' ? onNodeSelect(feature.id) : onRouteSelect(feature.id)} type="button">
            Open {feature.label}
          </button>
        ))}
      </div>
      {drawMode && <div className="atlas-drawing-notice" role="status">{drawMode === 'Rectangle' ? 'Click two search corners.' : 'Click the globe to add note coordinates.'} <button className="atlas-tool" type="button" onClick={onFinishDraw}>Finish drawing</button></div>}
      <div className="atlas-camera-tools" role="group" aria-label="Globe camera controls">
        <button className="atlas-tool" type="button" onClick={() => { lastFlownRef.current = selectedId; mapRef.current?.flyTo({ center: [30, 25], zoom: mapRef.current && mapRef.current.getContainer().clientWidth < 768 ? 1.0 : 1.8, bearing: 0, pitch: 0, duration: reducedMotion ? 0 : 1100 }); }}>Reset globe</button>
        <button className="atlas-tool" type="button" onClick={() => mapRef.current?.easeTo({ bearing: 0, duration: reducedMotion ? 0 : 500 })}>North up</button>
        <button className="atlas-tool" type="button" onClick={() => { const map = mapRef.current; map?.easeTo({ pitch: map.getPitch() > 10 ? 0 : 35, duration: reducedMotion ? 0 : 700 }); }}>Tilt</button>
        <button className="atlas-tool" type="button" aria-expanded={legendOpen} aria-controls="atlas-map-legend" onClick={() => setLegendOpen(!legendOpen)}>Legend</button>
      </div>
      <div id="atlas-map-legend" hidden={!legendOpen}><MapLegend
        civilizations={civilizations.map((civilization) => ({
          id: civilization.id,
          label: civilization.label,
          color: civilization.color,
        }))}
        showExtents={showExtents}
        showNodes={showNodes}
        showRoutes={showRoutes}
      /></div>
    </div>
  );
}
