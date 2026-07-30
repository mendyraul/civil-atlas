'use client';

import { useEffect, useMemo, useRef } from 'react';
import maplibregl, { GeoJSONSource, LngLatBounds, MapMouseEvent } from 'maplibre-gl';
import { NODE_VISIBILITY_ZOOM } from '../../lib/atlas';
import type { AtlasNode, AtlasRoute, Civilization } from '../../types/atlas';
import { MapLegend } from './MapLegend';

const MAP_STYLE = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

type AtlasMapProps = {
  civilizations: Civilization[];
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
};

type HoverRef = { source: string; id: string } | null;

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

// A7: selected extent stays prominent while others recede; no selection = uniform.
function fillOpacityExpression(selectedId?: string): maplibregl.ExpressionSpecification {
  const target = selectedId ?? '';
  return [
    'case',
    ['boolean', ['feature-state', 'hover'], false],
    0.34,
    ['==', ['get', 'id'], target],
    0.28,
    target.length > 0 ? 0.08 : 0.2,
  ];
}

function lineWidthExpression(selectedId?: string): maplibregl.ExpressionSpecification {
  return [
    'interpolate',
    ['linear'],
    ['zoom'],
    1,
    ['case', ['==', ['get', 'id'], selectedId ?? ''], 2.4, 0.7],
    5,
    ['case', ['==', ['get', 'id'], selectedId ?? ''], 3.6, 1.1],
  ];
}

function lineOpacityExpression(selectedId?: string): maplibregl.ExpressionSpecification {
  const target = selectedId ?? '';
  return [
    'case',
    ['boolean', ['feature-state', 'hover'], false],
    0.72,
    ['==', ['get', 'id'], target],
    0.64,
    target.length > 0 ? 0.12 : 0.28,
  ];
}

export function AtlasMap({
  civilizations,
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
}: AtlasMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const hoverRef = useRef<HoverRef>(null);
  const popupRef = useRef<maplibregl.Popup | null>(null);
  const lastFlownRef = useRef<string | undefined>(undefined);

  // Keep the latest callbacks in a ref so the map init effect can run exactly once.
  const handlersRef = useRef({
    onCivilizationSelect,
    onNodeSelect,
    onRouteSelect,
    onZoomChange,
  });
  handlersRef.current = {
    onCivilizationSelect,
    onNodeSelect,
    onRouteSelect,
    onZoomChange,
  };

  const polygonData = useMemo(
    () => polygonFeatureCollection(civilizations),
    [civilizations],
  );
  const pointData = useMemo(() => nodeFeatureCollection(nodes), [nodes]);
  const routeData = useMemo(() => routeFeatureCollection(routes), [routes]);

  // A1 + init: create the map once and register interaction handlers.
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: MAP_STYLE,
      center: [30, 25],
      zoom: 1.7,
      attributionControl: false,
    });

    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right');

    const popup = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
      offset: 12,
      className: 'atlas-hover-popup',
    });
    popupRef.current = popup;

    const clearHover = () => {
      if (hoverRef.current) {
        map.setFeatureState(hoverRef.current, { hover: false });
        hoverRef.current = null;
      }
      popup.remove();
      map.getCanvas().style.cursor = '';
    };

    map.on('load', () => {
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

      map.addSource('civilizations', { type: 'geojson', data: polygonData, promoteId: 'id' });
      map.addSource('nodes', { type: 'geojson', data: pointData, promoteId: 'id' });
      map.addSource('routes', { type: 'geojson', data: routeData, promoteId: 'id' });

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
            ['case', ['==', ['get', 'id'], selectedId ?? ''], 12, 7],
            5,
            ['case', ['==', ['get', 'id'], selectedId ?? ''], 18, 10],
          ],
          'line-opacity': [
            'case',
            ['==', ['get', 'id'], selectedId ?? ''],
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
          'fill-opacity': fillOpacityExpression(selectedId),
          // A4: cross-fade extents when the active year (and thus features) changes.
          'fill-opacity-transition': { duration: 450, delay: 0 },
        },
      });

      map.addLayer({
        id: 'civilizations-line',
        type: 'line',
        source: 'civilizations',
        layout: { 'line-cap': 'round', 'line-join': 'round' },
        paint: {
          'line-color': ['get', 'color'],
          'line-width': lineWidthExpression(selectedId),
          'line-opacity': lineOpacityExpression(selectedId),
          'line-blur': 0.6,
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
        const id = asId(event, 'civilizations-fill');
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
          const id = feature?.properties?.id;
          if (typeof id !== 'string') return;

          const source = sourceForLayer[layerId];
          if (hoverRef.current && (hoverRef.current.id !== id || hoverRef.current.source !== source)) {
            map.setFeatureState(hoverRef.current, { hover: false });
          }
          hoverRef.current = { source, id };
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
      handlersRef.current.onZoomChange(map.getZoom());
    });

    return () => {
      popup.remove();
      popupRef.current = null;
      map.remove();
      mapRef.current = null;
      hoverRef.current = null;
    };
  }, []);

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

  // A4: fade extents in whenever the set of visible civilizations changes.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded() || !map.getLayer('civilizations-fill')) return;
    map.setPaintProperty('civilizations-fill', 'fill-opacity', 0);
    const frame = requestAnimationFrame(() => {
      const current = mapRef.current;
      if (!current || !current.getLayer('civilizations-fill')) return;
      current.setPaintProperty(
        'civilizations-fill',
        'fill-opacity',
        fillOpacityExpression(selectedId),
      );
    });
    return () => cancelAnimationFrame(frame);
  }, [polygonData, selectedId]);

  // A7 + selection outline: emphasize the selected civilization.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded() || !map.getLayer('civilizations-line')) return;
    map.setPaintProperty('civilizations-line', 'line-width', lineWidthExpression(selectedId));
    map.setPaintProperty('civilizations-line', 'line-opacity', lineOpacityExpression(selectedId));
    map.setPaintProperty('civilizations-fill', 'fill-opacity', fillOpacityExpression(selectedId));
    map.setPaintProperty('civilizations-outline-glow', 'line-width', [
      'interpolate',
      ['linear'],
      ['zoom'],
      1,
      ['case', ['==', ['get', 'id'], selectedId ?? ''], 12, 7],
      5,
      ['case', ['==', ['get', 'id'], selectedId ?? ''], 18, 10],
    ]);
    map.setPaintProperty('civilizations-outline-glow', 'line-opacity', [
      'case',
      ['==', ['get', 'id'], selectedId ?? ''],
      0.18,
      0.1,
    ]);
  }, [selectedId]);

  // A2: fly the camera to frame the newly selected feature.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded() || !selectedId) return;
    if (lastFlownRef.current === selectedId) return;

    const civilization = civilizations.find((item) => item.id === selectedId);
    const node = nodes.find((item) => item.id === selectedId);
    const route = routes.find((item) => item.id === selectedId);

    if (civilization && civilization.polygon.length > 0) {
      const bounds = civilization.polygon.reduce(
        (acc, coordinate) => acc.extend(coordinate),
        new LngLatBounds(civilization.polygon[0], civilization.polygon[0]),
      );
      map.fitBounds(bounds, { padding: 96, maxZoom: 5, duration: 900 });
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
  }, [selectedId, civilizations, nodes, routes]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    map.setLayoutProperty('civilizations-outline-glow', 'visibility', showExtents ? 'visible' : 'none');
    map.setLayoutProperty('civilizations-fill', 'visibility', showExtents ? 'visible' : 'none');
    map.setLayoutProperty('civilizations-line', 'visibility', showExtents ? 'visible' : 'none');
  }, [showExtents]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    const visibility = showNodes ? 'visible' : 'none';
    map.setLayoutProperty('nodes-halo', 'visibility', visibility);
    map.setLayoutProperty('nodes-circle', 'visibility', visibility);
    map.setLayoutProperty('nodes-label', 'visibility', visibility);
  }, [showNodes]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    const visibility = showRoutes ? 'visible' : 'none';
    map.setLayoutProperty('routes-glow', 'visibility', visibility);
    map.setLayoutProperty('routes-line', 'visibility', visibility);
  }, [showRoutes]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    const selectedNodeIds = new Set<string>();
    nodes.forEach((node) => {
      if (evidenceIds.some((id) => node.evidence.some((record) => record.id === id))) {
        selectedNodeIds.add(node.id);
      }
    });

    (map.getSource('selected-evidence') as GeoJSONSource | undefined)?.setData({
      type: 'FeatureCollection',
      features: nodes
        .filter((node) => selectedNodeIds.has(node.id))
        .map((node) => ({
          type: 'Feature' as const,
          properties: { id: node.id },
          geometry: {
            type: 'Point' as const,
            coordinates: node.coordinates,
          },
        })),
    });

    map.setLayoutProperty('selected-evidence-glow', 'visibility', showEvidence ? 'visible' : 'none');
  }, [evidenceIds, nodes, showEvidence]);

  return (
    <div className="relative h-[68vh] min-h-[560px] w-full">
      <div className="h-full w-full" ref={containerRef} />
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
