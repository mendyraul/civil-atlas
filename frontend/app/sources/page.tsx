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
      <section className="atlas-panel mb-6 rounded-[24px] p-6" aria-labelledby="licenses-title">
        <p className="atlas-kicker">Open history</p>
        <h1 id="licenses-title" className="mt-2 text-3xl font-semibold">Data sources & licenses</h1>
        <p className="mt-4 max-w-3xl text-sm leading-7 text-slate-300">Civil Atlas code is licensed under AGPL-3.0-or-later, the published database under ODbL 1.0, and documentation under CC BY 4.0. Upstream data keeps its own license and attribution. Availability in this catalog does not mean a dataset is currently visible on the map.</p>
        <div className="mt-4 flex flex-wrap gap-4 text-sm text-cyan-200 underline"><a href="https://github.com/mendyraul/civil-atlas/blob/main/LICENSE">Code license</a><a href="https://github.com/mendyraul/civil-atlas/blob/main/DATA_LICENSE.md">Database license</a><a href="https://github.com/mendyraul/civil-atlas/blob/main/LICENSES/CC-BY-4.0.txt">Documentation license</a><a href="https://github.com/mendyraul/civil-atlas/blob/main/ATTRIBUTION.md">Full attribution register</a></div>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <article className="rounded-xl border border-white/10 p-4"><h2 className="font-semibold">Basemap · OpenStreetMap</h2><p className="mt-2 text-sm text-slate-300">© OpenStreetMap contributors. Basemap tiles provided by OpenFreeMap. Modern geographic context; labels and boundaries are not historical claims.</p><a className="mt-3 block text-sm text-cyan-200 underline" href="https://www.openstreetmap.org/copyright">ODbL 1.0 & attribution ↗</a></article>
          <article className="rounded-xl border border-white/10 p-4"><h2 className="font-semibold">Places · Pleiades</h2><p className="mt-2 text-sm text-slate-300">Places: Pleiades, © the Pleiades contributors, CC BY 3.0. Individual records retain their contributors and citations.</p><a className="mt-3 block text-sm text-cyan-200 underline" href="https://pleiades.stoa.org">Pleiades ↗</a><a className="mt-2 block text-sm text-cyan-200 underline" href="https://creativecommons.org/licenses/by/3.0/">CC BY 3.0 ↗</a></article>
          <article className="rounded-xl border border-white/10 p-4"><h2 className="font-semibold">Borders · Cliopatria</h2><p className="mt-2 text-sm text-slate-300">Borders: Cliopatria, Seshat Global History Databank (Bennett et al., Scientific Data 12, 247, 2025), CC BY 4.0. Imported interpretations become available on the atlas after review and publication.</p><a className="mt-3 block text-sm text-cyan-200 underline" href="https://doi.org/10.1038/s41597-025-04516-9">Paper & citation ↗</a><a className="mt-2 block text-sm text-cyan-200 underline" href="https://github.com/Seshat-Global-History-Databank/cliopatria">Dataset releases ↗</a><a className="mt-2 block text-sm text-cyan-200 underline" href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0 ↗</a></article>
        </div>
        <details className="mt-5 rounded-xl border border-white/10 p-4"><summary>Planned sources · not included in the current dataset</summary><ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-300"><li><a className="text-cyan-200 underline" href="https://www.openhistoricalmap.org">OpenHistoricalMap</a> · CC0. Credit appreciated: © OpenHistoricalMap contributors.</li><li><a className="text-cyan-200 underline" href="https://www.itiner-e.org">Itiner-e, Digital Atlas of Ancient Roads</a> · CC BY 4.0.</li><li><a className="text-cyan-200 underline" href="https://github.com/AWMC/geodata">Ancient World Mapping Center geodata</a> · ODbL 1.0.</li><li><a className="text-cyan-200 underline" href="https://www.wikidata.org">Wikidata</a> · CC0.</li></ul><p className="mt-3 text-sm">These entries mirror the planned section of the attribution register; each import must pass source review before it appears on the map.</p></details>
        <p className="mt-5 text-sm text-slate-300">Retain upstream credits when reusing the database or creating maps and other produced works. Consult the attribution register for release details and modification notices.</p>
      </section>
      <h2 className="mb-4 text-xl font-semibold">Published evidence records</h2>
      {sources.length === 0 && <p className="mb-4 text-slate-300">No evidence records are currently available from the configured data channel.</p>}
      <section className="grid gap-4 lg:grid-cols-2">
        {sources.map((source) => (
          <article className="atlas-panel scroll-mt-4 rounded-[24px] p-5" id={source.id} key={source.id}>
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
