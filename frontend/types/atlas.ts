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
  polygon: [number, number][];
  evidence: EvidenceRecord[];
};

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

export type WorldPayload = {
  year: number;
  civilizations: Civilization[];
  nodes: AtlasNode[];
  routes: AtlasRoute[];
};

export type AtlasFeature = Civilization | AtlasNode | AtlasRoute;

export type SourceRecord = {
  id: string;
  featureId: string;
  featureKind: AtlasFeature['kind'];
  featureLabel: string;
  title: string;
  citation: string;
  link?: string;
  confidence: Confidence;
  reviewStatus: ReviewStatus;
  notes: string;
};
