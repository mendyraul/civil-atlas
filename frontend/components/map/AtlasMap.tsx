'use client';

import { useEffect, useMemo, useRef } from 'react';
import maplibregl, { GeoJSONSource, MapMouseEvent } from 'maplibre-gl';
import { NODE_VISIBILITY_ZOOM } from '../../lib/atlas';
import type { AtlasNode, AtlasRoute, Civilization } from '../../types/atlas';

const MAP_STYLE = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json';

type AtlasMapProps = {
  civilizations: Civilization[];
  nodes: AtlasNode[];
  routes: AtlasRoute[];
  selectedId?: string;
  onCivilizationSelect: (id: string) => void;
  onNodeSelect: (id: string) => void;
  onRouteSelect: (id: string) => void;
  onZoomChange: (zoom: number) => void;
};

function polygonFeatureCollection(items: Civilization[]) {
  return {
    type: 'FeatureCollection' as const,
    features: items.map((civilization) => ({
      type: 'Feature' as const,
      id: civilization.id,
      properties: {
        id: civilization.id,
        label: civilization.label,
        color: civilization.color,
      },
      geometry: {
        type: 'Polygon' as const,
        coordinates: [[...civilization.polygon]],
      },
    })),
  };
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

export function AtlasMap({
  civilizations,
  nodes,
  routes,
  selectedId,
  onCivilizationSelect,
  onNodeSelect,
  onRouteSelect,
  onZoomChange,
}: AtlasMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);

  const polygonData = useMemo(
    () => polygonFeatureCollection(civilizations),
    [civilizations],
  );
  const pointData = useMemo(() => nodeFeatureCollection(nodes), [nodes]);
  const routeData = useMemo(() => routeFeatureCollection(routes), [routes]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: MAP_STYLE,
      center: [38, 28],
      zoom: 2.1,
      attributionControl: false,
    });

    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl(), 'top-right');

    map.on('load', () => {
      map.addSource('civilizations', { type: 'geojson', data: polygonData });
      map.addSource('nodes', { type: 'geojson', data: pointData });
      map.addSource('routes', { type: 'geojson', data: routeData });

      map.addLayer({
        id: 'routes-line',
        type: 'line',
        source: 'routes',
        paint: {
          'line-color': '#123f73',
          'line-width': ['interpolate', ['linear'], ['zoom'], 1, 1, 4, 2, 7, 3],
          'line-opacity': 0.72,
          'line-dasharray': [2, 1.4],
        },
      });

      map.addLayer({
        id: 'civilizations-fill',
        type: 'fill',
        source: 'civilizations',
        paint: {
          'fill-color': ['get', 'color'],
          'fill-opacity': 0.28,
        },
      });

      map.addLayer({
        id: 'civilizations-line',
        type: 'line',
        source: 'civilizations',
        paint: {
          'line-color': ['get', 'color'],
          'line-width': ['case', ['==', ['get', 'id'], selectedId ?? ''], 3, 1.2],
          'line-opacity': 0.9,
        },
      });

      map.addLayer({
        id: 'nodes-circle',
        type: 'circle',
        source: 'nodes',
        minzoom: NODE_VISIBILITY_ZOOM,
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['zoom'], NODE_VISIBILITY_ZOOM, 4, 7, 8],
          'circle-color': '#13263c',
          'circle-stroke-color': '#fff6e8',
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
          'text-color': '#13263c',
          'text-halo-color': '#fff8ec',
          'text-halo-width': 1.1,
        },
      });

      const asId = (event: MapMouseEvent, layerId: string) =>
        map.queryRenderedFeatures(event.point, { layers: [layerId] })[0]?.properties?.id;

      map.on('click', 'civilizations-fill', (event) => {
        const id = asId(event, 'civilizations-fill');
        if (typeof id === 'string') onCivilizationSelect(id);
      });

      map.on('click', 'nodes-circle', (event) => {
        const id = asId(event, 'nodes-circle');
        if (typeof id === 'string') onNodeSelect(id);
      });

      map.on('click', 'routes-line', (event) => {
        const id = asId(event, 'routes-line');
        if (typeof id === 'string') onRouteSelect(id);
      });

      map.on('zoom', () => onZoomChange(map.getZoom()));
      onZoomChange(map.getZoom());
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [onCivilizationSelect, onNodeSelect, onRouteSelect, onZoomChange, pointData, polygonData, routeData, selectedId]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    (map.getSource('civilizations') as GeoJSONSource | undefined)?.setData(polygonData);
  }, [polygonData]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    (map.getSource('nodes') as GeoJSONSource | undefined)?.setData(pointData);
  }, [pointData]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    (map.getSource('routes') as GeoJSONSource | undefined)?.setData(routeData);
  }, [routeData]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded() || !map.getLayer('civilizations-line')) return;
    map.setPaintProperty('civilizations-line', 'line-width', [
      'case',
      ['==', ['get', 'id'], selectedId ?? ''],
      3,
      1.2,
    ]);
  }, [selectedId]);

  return <div className="h-[68vh] min-h-[560px] w-full" ref={containerRef} />;
}
