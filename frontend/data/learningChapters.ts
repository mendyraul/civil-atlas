import type { LearningChapter } from '../types/atlas';

export const learningChapters: LearningChapter[] = [
  {
    id: 'connected-world-117',
    title: 'A connected world in 117 CE',
    summary: 'Read empires as changing systems of places, routes, evidence, and contested reach.',
    objectives: [
      'Distinguish direct control from influence and exchange.',
      'Connect a map transition to the claim and sources behind it.',
      'Describe historical dates as estimates when the evidence requires it.',
    ],
    steps: [
      {
        id: 'trajanic-moment',
        title: 'A campaign moment, not a timeless border',
        narrative: 'The Roman extent at 117 CE captures the brief high-water mark of Trajan’s eastern campaigns.',
        year: 117,
        selectedEntityId: 'roman-empire',
        camera: { center: [25, 38], zoom: 2.7 },
        visibleLayers: ['extents', 'nodes', 'sources'],
        annotations: ['Compare the imperial core with the eastern campaign frontier.', 'The polygon is an approximate interpretation.'],
        question: 'Which parts of this view may represent military reach rather than durable administration?',
        sourcePrompt: 'Open the selected polity’s evidence and compare the chronology with the mapped extent.',
      },
      {
        id: 'corridors-of-influence',
        title: 'Corridors carry influence',
        narrative: 'Han activity in the Western Regions is better understood as changing corridor influence than as a crisp border.',
        year: 123,
        selectedEntityId: 'han-dynasty',
        camera: { center: [105, 35], zoom: 2.8 },
        visibleLayers: ['extents', 'nodes', 'routes', 'sources'],
        annotations: ['Routes are interpretive connections, not proof of uniform control.'],
        question: 'How does adding routes change what “extent” appears to mean?',
        sourcePrompt: 'Inspect the event evidence and ask which dates mark processes rather than instantaneous change.',
      },
      {
        id: 'red-sea-system',
        title: 'An inland–port system',
        narrative: 'Aksum and Adulis show why cities and exchange networks belong beside territorial layers.',
        year: 130,
        selectedEntityId: 'aksumite-kingdom',
        camera: { center: [39, 14], zoom: 4.2 },
        visibleLayers: ['extents', 'nodes', 'routes', 'sources'],
        annotations: ['The exchange intensification is estimated between 50 and 150 CE.'],
        question: 'What evidence would you need before assigning an exact start year?',
        sourcePrompt: 'Follow the source prompt in the event log and note the confidence label.',
      },
    ],
  },
];
