import catalog from './catalog.json';
import { civilizationColor } from '../../lib/palette';
import type { Civilization, SourceRecord } from '../../types/atlas';

export const historicalCatalog = catalog;
const citation = 'Bennett et al., Cliopatria, Scientific Data 12, 247 (2025), doi:10.1038/s41597-025-04516-9. ' + catalog.release + '. Seshat Global History Databank. CC BY 4.0.';

export const historicalSources: SourceRecord[] = catalog.rows.map((row) => ({
  id: row.sourceRecordId, featureId: row.id, featureKind: 'civilization_layer', featureLabel: row.name,
  title: `Cliopatria: ${row.name}`, citation: `${citation} ${row.name}: ${row.validFromYear} to ${row.validToYear}; Wikidata ${row.wikidata}.`,
  link: catalog.upstreamUrl, sourceNamespace: 'cliopatria', confidence: 'low', reviewStatus: catalog.reviewStatus as 'reviewed' | 'needs_review',
  validFromYear: row.validFromYear, validToYear: row.validToYear, notes: `${catalog.reviewScope} ${catalog.coverage}`,
}));

export const historicalCivilizations: Civilization[] = [...new Set(catalog.rows.map((row) => row.civilizationId))].map((id) => {
  const rows = catalog.rows.filter((row) => row.civilizationId === id);
  const name = rows[0].name;
  const startYear = Math.min(...rows.map((row) => row.validFromYear)), endYear = Math.max(...rows.map((row) => row.validToYear));
  return {
    id, slug: id, kind: 'civilization', label: name, displayName: name, startYear, endYear,
    civilizationType: name.includes('Dynasty') ? 'dynasty' : name.includes('Kingdom') ? 'kingdom' : /Empire|Caliphate/.test(name) ? 'empire' : 'civilization',
    color: civilizationColor(id), colorToken: id, capital: 'Not specified by this source',
    summary: `Explore dated territorial interpretations of ${name} from Cliopatria.`,
    shortDescription: `Source-reported territory with dated boundary changes.`,
    panelDescription: `${catalog.reviewScope} ${catalog.coverage}`,
    extentNote: 'Original source coordinates; approximate historical frontiers.',
    confidence: 'low', reviewStatus: catalog.reviewStatus as 'reviewed' | 'needs_review',
    sourceNotes: citation, statusBadges: ['Approximate', 'Source-reported'],
    evidence: [{ id: `cliopatria-polity-${id}`, title: `Cliopatria: ${name}`, citation, link: catalog.upstreamUrl,
      confidence: 'low', reviewStatus: catalog.reviewStatus as 'reviewed' | 'needs_review', notes: catalog.reviewScope }],
  };
});
