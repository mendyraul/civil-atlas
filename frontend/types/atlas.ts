export type Confidence = 'low' | 'medium' | 'medium_high' | 'high';
export type ReviewStatus =
  | 'placeholder'
  | 'seeded'
  | 'needs_review'
  | 'reviewed';
export type NodeKind =
  | 'city'
  | 'port'
  | 'route_hub'
  | 'frontier'
  | 'religious_center'
  | 'administrative_center';
export type RouteKind =
  | 'road'
  | 'sea_route'
  | 'trade_route'
  | 'military_route'
  | 'river_route';
export type CivilizationType =
  | 'empire'
  | 'dynasty'
  | 'kingdom'
  | 'civilization';
export type PlaceRole =
  | 'capital'
  | 'major_city'
  | 'port'
  | 'trade_hub'
  | 'religious_center'
  | 'administrative_center'
  | 'frontier_post';
export type HistoricalEventType =
  | 'annexation'
  | 'campaign'
  | 'capital_move'
  | 'trade_shift'
  | 'religious_change'
  | 'frontier_change'
  | 'urban_peak';
export type LayerType =
  | 'direct_control'
  | 'source_reported_extent'
  | 'trade_network'
  | 'cultural_extent'
  | 'influence_zone'
  | 'contested_zone'
  | 'administrative_layer'
  | 'thematic_overlay';
export type InterpretationKind =
  | 'boundary_variant'
  | 'influence_zone'
  | 'contested_zone'
  | 'administrative_layer'
  | 'thematic_overlay';
export type RelationshipType =
  | 'contested_frontier'
  | 'trade_exchange'
  | 'influence_overlap'
  | 'cultural_exchange';

export type EvidenceRecord = {
  id: string;
  title: string;
  citation: string;
  link?: string;
  confidence: Confidence;
  reviewStatus: ReviewStatus;
  notes: string;
};

export type StatusBadge =
  | 'Approximate'
  | 'Source-reported'
  | 'Placeholder geometry'
  | 'Needs review'
  | 'Reviewed';

export type Civilization = {
  id: string;
  slug: string;
  kind: 'civilization';
  label: string;
  displayName: string;
  startYear: number;
  endYear: number;
  civilizationType: CivilizationType;
  color: string;
  colorToken: string;
  summary: string;
  shortDescription: string;
  capital: string;
  panelDescription: string;
  extentNote: string;
  confidence: Confidence;
  reviewStatus: ReviewStatus;
  sourceNotes: string;
  statusBadges: StatusBadge[];
  /** @deprecated Seed-authoring aid only. Never render territorial graphics from this field. */
  polygon?: GeoJSONPosition[];
  evidence: EvidenceRecord[];
};

export type GeoJSONPosition = [longitude: number, latitude: number];
export type PolygonGeometry = {
  type: 'Polygon';
  /** Exterior ring followed by zero or more interior rings (holes). */
  coordinates: GeoJSONPosition[][];
};
export type MultiPolygonGeometry = {
  type: 'MultiPolygon';
  coordinates: GeoJSONPosition[][][];
};
export type TerritorialGeometry = PolygonGeometry | MultiPolygonGeometry;

export type AtlasNode = {
  id: string;
  slug: string;
  kind: 'node';
  label: string;
  name: string;
  modernName?: string;
  nodeKind: NodeKind;
  placeType: NodeKind;
  role: PlaceRole;
  civilizationId?: string;
  civilizationSlug?: string;
  startYear: number;
  endYear: number;
  summary: string;
  coordinates: [number, number];
  confidence: Confidence;
  reviewStatus: ReviewStatus;
  sourceNotes: string;
  statusBadges: StatusBadge[];
  evidence: EvidenceRecord[];
};

export type AtlasRoute = {
  id: string;
  slug: string;
  kind: 'route';
  label: string;
  routeKind: RouteKind;
  edgeType: RouteKind;
  sourceNodeId: string;
  targetNodeId: string;
  civilizationIds: string[];
  startYear: number;
  endYear: number;
  summary: string;
  path: [number, number][];
  confidence: Confidence;
  reviewStatus: ReviewStatus;
  sourceNotes: string;
  statusBadges: StatusBadge[];
  evidence: EvidenceRecord[];
};

export type CivilizationLayer = {
  id: string;
  civilizationId: string;
  name: string;
  layerType: LayerType;
  variantGroup?: string;
  interpretationLabel?: string;
  interpretationKind?: InterpretationKind;
  isPrimary: boolean;
  displayOrder: number;
  validFromYear: number;
  validToYear: number;
  geometryJson: TerritorialGeometry;
  geometryPlaceholder?: string;
  isPlaceholder?: boolean;
  confidence: Confidence;
  reviewStatus: ReviewStatus;
  sourceNote: string;
  sourceRecordIds: string[];
  claimIds: string[];
};

export type HistoricalRelationship = {
  id: string;
  relationshipType: RelationshipType;
  subjectId: string;
  subjectKind: 'civilization' | 'place' | 'civilization_layer';
  targetId: string;
  targetKind: 'civilization' | 'place' | 'civilization_layer';
  label: string;
  summary: string;
  validFromYear: number;
  validToYear: number;
  confidence: Confidence;
  reviewStatus: ReviewStatus;
  sourceNote: string;
  sourceRecordIds: string[];
  claimIds: string[];
};

export type Era = {
  id: string;
  slug: string;
  label: string;
  startYear: number;
  endYear: number;
  summary: string;
  focusRegion: string;
  featuredCivilizationIds: string[];
  confidence: Confidence;
  reviewStatus: ReviewStatus;
  evidence: EvidenceRecord[];
};

export type HistoricalEvent = {
  id: string;
  slug: string;
  label: string;
  eventType: HistoricalEventType;
  startYear: number;
  endYear: number;
  displayDate: string;
  /** How the displayed date should be interpreted, rather than assuming a single instant. */
  datePrecision?: 'exact' | 'circa' | 'interval';
  dateUncertainty?: string;
  transitionClaim?: string;
  responsibleLayerIds?: string[];
  summary: string;
  impact: string;
  civilizationIds: string[];
  placeIds: string[];
  confidence: Confidence;
  reviewStatus: ReviewStatus;
  evidence: EvidenceRecord[];
};

export type AtlasCamera = {
  center: [number, number];
  zoom: number;
  bearing?: number;
  pitch?: number;
};

export type LearningStep = {
  id: string;
  title: string;
  narrative: string;
  year: number;
  selectedEntityId?: string;
  camera: AtlasCamera;
  visibleLayers: Array<'extents' | 'nodes' | 'routes' | 'sources'>;
  annotations: string[];
  question?: string;
  sourcePrompt: string;
};

export type LearningChapter = {
  id: string;
  title: string;
  summary: string;
  objectives: string[];
  steps: LearningStep[];
};

export type WorldPayload = {
  year: number;
  civilizations: Civilization[];
  nodes: AtlasNode[];
  routes: AtlasRoute[];
  layers: CivilizationLayer[];
  relationships: HistoricalRelationship[];
  eras: Era[];
  events: HistoricalEvent[];
};

export type AtlasFeature = Civilization | AtlasNode | AtlasRoute;

export type SourceRecord = {
  sourceNamespace?: string;
  validFromYear?: number;
  validToYear?: number;
  id: string;
  featureId: string;
  featureKind: AtlasFeature['kind'] | 'civilization_layer' | 'era' | 'event';
  featureLabel: string;
  title: string;
  citation: string;
  link?: string;
  confidence: Confidence;
  reviewStatus: ReviewStatus;
  notes: string;
};

export type LayerStatus = {
  delivery: 'loading' | 'ready' | 'unavailable' | 'demo';
  year: number;
  recordCount: number;
  layers: CivilizationLayer[];
};
export type MapAnnotation = {
  id: string;
  title: string;
  note: string;
  validFromYear: number;
  validToYear: number;
  geometry?: { type: 'Point'; coordinates: GeoJSONPosition } | { type: 'LineString'; coordinates: GeoJSONPosition[] } | TerritorialGeometry;
  boundaryLayerId?: string;
  sourceRecordIds: string[];
  kind: 'explanation' | 'territory';
  reviewStatus: 'needs_review' | 'reviewed' | 'rejected';
  confidence: Confidence;
};
export type EpisodeAsset = {
  id: string; kind: 'image' | 'audio' | 'video'; path: string; attribution: string; license: string;
  sha256: string; byteLength: number; bounds?: [number, number, number, number]; coordinates?: GeoJSONPosition;
};
export type EpisodePack = {
  schemaVersion: 1; id: string; title: string; summary: string; datasetVersion: string;
  attribution: string; license: 'ODbL-1.0'; reviewStatus: 'needs_review' | 'reviewed' | 'rejected';
  steps: Array<{ id: string; title: string; narrative: string; year: number; camera: AtlasCamera; entityIds: string[]; layerIds: string[]; annotationIds: string[]; assetIds: string[]; sourceRecordIds: string[]; holdSeconds: number }>;
  annotations: MapAnnotation[]; assets: EpisodeAsset[];
};
export type ComparisonState = { leftYear: number; rightYear: number; leftLayer: string; rightLayer: string; linked: boolean; camera: AtlasCamera };
export type ResearchArea = { bbox: [number, number, number, number] } | { center: GeoJSONPosition; radiusKm: number } | { layerId: string };
export type ResearchQuery = { operation: 'entities_in_area' | 'events_in_area' | 'compare_boundaries' | 'sources_for_feature' | 'episodes' | 'atlas_link'; year: number; area?: ResearchArea; kinds?: string[]; page?: number; pageSize?: number; featureId?: string; leftLayerId?: string; rightLayerId?: string; rightYear?: number };
export type ResearchResult = { summary: string; items: Array<{ kind?: string; record?: Record<string, unknown>; sources?: SourceRecord[]; url?: string; title?: string; citation?: string; id?: string }>; total: number; page: number; pageSize: number; dataVersion: string; limitations: string[]; unlocatedCount: number };
