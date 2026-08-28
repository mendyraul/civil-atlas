import { notFound } from 'next/navigation';
import { SiteShell } from '../../../components/atlas/SiteShell';
import { API_BASE_URL, formatYear } from '../../../lib/atlas';

export const dynamic = 'force-dynamic';

type Entity = {
  id: string;
  slug: string;
  kind: string;
  canonical_name: string;
  valid_from_year?: number | null;
  valid_to_year?: number | null;
  review_state: string;
  overview_claim_ids: string[];
  passage_ids: string[];
  map_layers: Array<{ id?: string; label?: string }>;
  related_entity_ids: string[];
};

type Claim = {
  id: string;
  version: number;
  predicate: string;
  object_id?: string | null;
  value?: string | number | boolean | Record<string, unknown> | null;
  valid_from_year?: number | null;
  valid_to_year?: number | null;
  source_id: string;
  citation_locator: string;
  confidence: string;
  confidence_rationale: string;
  review_state: string;
};

async function fetchEntity(slug: string): Promise<{ entity: Entity; claims: Claim[] } | null> {
  if (!API_BASE_URL) return null;
  const response = await fetch(`${API_BASE_URL}/api/entities/${encodeURIComponent(slug)}`, { cache: 'no-store' });
  if (!response.ok) return null;
  const entity = (await response.json()) as Entity;
  const claims = await Promise.all(entity.overview_claim_ids.map(async (claimId) => {
    const claimResponse = await fetch(`${API_BASE_URL}/api/claims/${encodeURIComponent(claimId)}`, { cache: 'no-store' });
    return claimResponse.ok ? ((await claimResponse.json()) as Claim) : null;
  }));
  return { entity, claims: claims.filter((claim): claim is Claim => claim !== null) };
}

function dates(entity: Entity) {
  if (entity.valid_from_year == null || entity.valid_to_year == null) return 'Date range not recorded';
  return `${formatYear(entity.valid_from_year)}–${formatYear(entity.valid_to_year)}`;
}

export default async function EntityPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const result = await fetchEntity(slug);
  if (!result) notFound();
  const { entity, claims } = result;
  return (
    <SiteShell title={entity.canonical_name} subtitle="Evidence-first entity dossier">
      <main className="mx-auto max-w-7xl space-y-5">
        <section className="atlas-hero rounded-[32px] p-7 md:p-10">
          <div className="flex flex-wrap items-center gap-3">
            <span className="atlas-kicker">{entity.kind} dossier</span>
            <span className="rounded-full border border-emerald-300/25 bg-emerald-300/10 px-3 py-1 text-xs text-emerald-200">{entity.review_state.replace('_', ' ')}</span>
          </div>
          <h1 className="mt-5 text-4xl font-semibold tracking-tight md:text-6xl">{entity.canonical_name}</h1>
          <p className="mt-3 text-lg text-slate-400">{dates(entity)}</p>
        </section>
        <div className="grid gap-5 lg:grid-cols-2">
          <section className="atlas-panel rounded-[28px] p-6">
            <h2 className="text-xl font-semibold">Map layers</h2>
            <ul className="mt-5 space-y-3 text-slate-300">{entity.map_layers.length ? entity.map_layers.map((layer) => <li key={layer.id}>{layer.label ?? layer.id}</li>) : <li>No map layer is recorded.</li>}</ul>
          </section>
          <section className="atlas-panel rounded-[28px] p-6">
            <h2 className="text-xl font-semibold">Related records</h2>
            <p className="mt-5 text-sm leading-6 text-slate-300">{entity.related_entity_ids.length ? entity.related_entity_ids.join(' · ') : 'No related records are recorded.'}</p>
            {entity.passage_ids.length ? <p className="mt-4 text-sm leading-6 text-slate-400">Primary passages: {entity.passage_ids.join(' · ')}</p> : null}
          </section>
        </div>
        <section className="atlas-panel rounded-[30px] p-7">
          <p className="atlas-kicker">Evidence path</p>
          <h2 className="mt-3 text-2xl font-semibold">Claims supporting this record</h2>
          <div className="mt-6 space-y-4">
            {claims.length ? claims.map((claim) => <article className="rounded-2xl border border-cyan-300/15 bg-cyan-300/5 p-5" key={`${claim.id}-${claim.version}`}>
              <div className="flex flex-wrap justify-between gap-3"><h3 className="font-medium">{claim.predicate.replaceAll('_', ' ')}</h3><span className="text-xs text-cyan-200">{claim.confidence} confidence · {claim.review_state.replace('_', ' ')}</span></div>
              <p className="mt-3 text-sm text-slate-300">{claim.value == null ? claim.object_id ?? 'Related record assertion' : typeof claim.value === 'object' ? JSON.stringify(claim.value) : String(claim.value)}</p>
              <p className="mt-3 text-xs leading-5 text-slate-400">Source: {claim.source_id} · {claim.citation_locator} · {claim.valid_from_year == null || claim.valid_to_year == null ? 'time bounds not recorded' : `${formatYear(claim.valid_from_year)}–${formatYear(claim.valid_to_year)}`}</p>
              <p className="mt-2 text-sm leading-6 text-slate-400">{claim.confidence_rationale}</p>
            </article>) : <p className="text-slate-400">No published claims are linked to this record.</p>}
          </div>
        </section>
      </main>
    </SiteShell>
  );
}
