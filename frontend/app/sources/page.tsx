import Link from 'next/link';
import { SiteShell } from '../../components/atlas/SiteShell';
import { evidenceTone, fetchSources, reviewTone } from '../../lib/atlas';

export default async function SourcesPage() {
  const sources = await fetchSources();

  return (
    <SiteShell
      title="Sources"
      subtitle="Evidence records are first-class. Every seeded civilization, place, and route exposes provenance, confidence, and review status from day one."
    >
      <section className="grid gap-4 lg:grid-cols-2">
        {sources.map((source) => (
          <article className="atlas-panel rounded-[24px] p-5" key={source.id}>
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-[--muted]">
                  {source.featureKind} · {source.featureLabel}
                </p>
                <h2 className="mt-2 text-xl font-semibold"><Link href={`/sources/${source.id}`}>{source.title}</Link></h2>
              </div>
            </div>
            <p className="mt-2 text-sm text-[--muted]">{source.citation}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              <span className={`rounded-full px-2.5 py-1 text-xs ${evidenceTone(source.confidence)}`}>
                {source.confidence} confidence
              </span>
              <span className={`rounded-full px-2.5 py-1 text-xs ${reviewTone(source.reviewStatus)}`}>
                {source.reviewStatus.replace('_', ' ')}
              </span>
            </div>
            <p className="mt-4 text-sm leading-6">{source.notes}</p>
          </article>
        ))}
      </section>
    </SiteShell>
  );
}
