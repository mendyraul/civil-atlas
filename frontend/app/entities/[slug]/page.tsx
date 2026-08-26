import Link from 'next/link';
import { notFound } from 'next/navigation';
import { SiteShell } from '../../../components/atlas/SiteShell';

const dossiers = {
  trajan: {
    name: 'Trajan', kind: 'Person', dates: '53–117 CE', state: 'Reviewed',
    assertion: 'Trajan held the office of Roman emperor from 98 to 117 CE.',
  },
};

export default async function EntityPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const entity = dossiers[slug as keyof typeof dossiers];
  if (!entity) notFound();
  return <SiteShell title={entity.name} subtitle="Evidence-first entity dossier">
    <main className="mx-auto max-w-7xl space-y-5">
      <section className="atlas-hero rounded-[32px] p-7 md:p-10">
        <div className="flex flex-wrap items-center gap-3"><span className="atlas-kicker">{entity.kind} dossier</span><span className="rounded-full border border-emerald-300/25 bg-emerald-300/10 px-3 py-1 text-xs text-emerald-200">{entity.state}</span></div>
        <h1 className="mt-5 text-4xl font-semibold tracking-tight md:text-6xl">{entity.name}</h1>
        <p className="mt-3 text-lg text-slate-400">{entity.dates} · Nerva–Antonine dynasty</p>
        <div className="mt-8 grid gap-4 lg:grid-cols-[1.5fr_1fr]">
          <article className="rounded-3xl border border-white/10 bg-black/20 p-6"><p className="atlas-kicker">Overview</p><p className="mt-4 text-xl leading-8 text-slate-100">{entity.assertion}</p><Link href="#belief-claim-trajan-office" className="mt-5 inline-flex rounded-full border border-cyan-300/30 bg-cyan-300/10 px-4 py-2 text-sm font-medium text-cyan-100">Why do we believe this? →</Link></article>
          <article className="rounded-3xl border border-white/10 bg-black/20 p-6"><p className="atlas-kicker">Map layers</p><div className="mt-4 flex h-40 items-end rounded-2xl border border-white/8 bg-[radial-gradient(circle_at_60%_40%,rgba(75,198,214,.3),transparent_20%),linear-gradient(145deg,#10263a,#09131f)] p-4"><span className="rounded-full bg-black/50 px-3 py-1 text-xs">Roman administration · 117 CE</span></div></article>
        </div>
      </section>
      <div className="grid gap-5 lg:grid-cols-2">
        <Panel title="Chronology"><Timeline year="98 CE" text="Accession following Nerva"/><Timeline year="101–106" text="Dacian campaigns"/><Timeline year="113–117" text="Eastern campaign and final years"/></Panel>
        <Panel title="Related entities"><Cards items={['Roman emperor · office','Nerva–Antonine · dynasty','Principate · concept','Trajan’s Column · artifact']}/></Panel>
        <Panel title="Source excerpts"><p className="text-slate-300">Cassius Dio, <em>Roman History</em> 68 — linked as a primary-source passage, with edition-specific locator and translation recorded separately.</p><p className="mt-4 text-xs text-slate-500">Locator: book 68, sections 4–5 · Source record available</p></Panel>
        <Panel title="Historiographical disagreements"><div className="rounded-2xl border border-amber-300/20 bg-amber-300/8 p-4"><p className="font-medium text-amber-100">Extent of direct administration</p><p className="mt-2 text-sm leading-6 text-slate-300">Competing map interpretations are preserved as claim-backed layers rather than merged into a single boundary.</p></div></Panel>
      </div>
      <section id="belief-claim-trajan-office" className="atlas-panel scroll-mt-5 rounded-[30px] p-7"><p className="atlas-kicker">Evidence path · claim v2</p><h2 className="mt-3 text-2xl font-semibold">Why do we believe this?</h2><div className="mt-6 grid gap-3 md:grid-cols-4"><Step n="1" title="Assertion" text="held_office: Roman emperor"/><Step n="2" title="Scope" text="98–117 CE · Roman world"/><Step n="3" title="Citation" text="Chronology §§4–5"/><Step n="4" title="Review" text="High confidence · reviewed"/></div><p className="mt-5 text-sm leading-6 text-slate-400"><strong className="text-slate-200">Rationale:</strong> Accession and death dates agree across the cited chronology and independent narrative tradition. This version supersedes claim v1; the revision remains visible.</p></section>
    </main>
  </SiteShell>;
}

function Panel({title, children}:{title:string;children:React.ReactNode}) { return <section className="atlas-panel rounded-[28px] p-6"><h2 className="text-xl font-semibold">{title}</h2><div className="mt-5">{children}</div></section> }
function Timeline({year,text}:{year:string;text:string}) { return <div className="grid grid-cols-[90px_1fr] border-l border-cyan-300/30 pb-5 pl-4 last:pb-0"><span className="text-sm text-cyan-200">{year}</span><span className="text-slate-300">{text}</span></div> }
function Cards({items}:{items:string[]}) { return <div className="grid gap-2 sm:grid-cols-2">{items.map(x=><div key={x} className="rounded-2xl border border-white/8 bg-white/4 p-4 text-sm text-slate-200">{x}</div>)}</div> }
function Step({n,title,text}:{n:string;title:string;text:string}) { return <div className="rounded-2xl border border-cyan-300/15 bg-cyan-300/5 p-4"><span className="text-xs text-cyan-200">0{n}</span><h3 className="mt-2 font-medium">{title}</h3><p className="mt-2 text-sm text-slate-400">{text}</p></div> }
