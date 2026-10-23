import { learningChapters } from './learningChapters';
import { world117 } from './demoWorld117';
import type { EpisodePack } from '../types/atlas';
// Demonstration only. No invented territorial geometry or publication status.
export const connectedWorldDemo: EpisodePack = {
  schemaVersion: 1, id: 'connected-world-117', title: 'A connected world around 117 CE',
  summary: 'Follow Rome, Han corridors, and the Red Sea. This local demonstration uses existing narratives; reviewed territorial coverage is supplied separately.',
  datasetVersion: 'connected-world-demo-v1', attribution: 'Civil Atlas contributors; see linked source records.', license: 'ODbL-1.0', reviewStatus: 'needs_review', assets: [], annotations: [],
  steps: learningChapters[0].steps.map((step) => ({ id: step.id, title: step.title, narrative: step.narrative, year: step.year, camera: step.camera, entityIds: step.selectedEntityId ? [step.selectedEntityId] : [], layerIds: [], annotationIds: [], assetIds: [], sourceRecordIds: world117.civilizations.find((c) => c.id === step.selectedEntityId)?.evidence.map((e) => e.id) ?? [], holdSeconds: 8 })),
};
