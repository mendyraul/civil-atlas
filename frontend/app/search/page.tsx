import Link from 'next/link';
import { SiteShell } from '../../components/atlas/SiteShell';
import { API_BASE_URL, DEMO_MODE, fetchCivilizations, fetchWorld } from '../../lib/atlas';

type Params = Record<string, string | string[] | undefined>;
export default async function SearchPage({ searchParams }: { searchParams: Promise<Params> }) {
  const input = await searchParams; const q = String(input.q ?? ''); const page = Math.max(1, Number(input.page ?? 1)); const sort = String(input.sort ?? 'relevance');
  const query = new URLSearchParams(); for (const key of ['q', 'start_year', 'end_year', 'region', 'polity_type', 'topic', 'confidence', 'review_status', 'sort']) { if (input[key]) query.set(key, String(input[key])); } query.set('page', String(page)); query.set('page_size', '12');
  let result: { items: Array<{ id: string; kind: string; slug: string; title: string; summary: string; aliases: string[] }>; total: number };
  if (API_BASE_URL && !DEMO_MODE) result = await fetch(`${API_BASE_URL}/api/v1/search?${query}`, { cache: 'no-store' }).then((response) => response.json());
  else { const world = await fetchWorld(); const items = [...await fetchCivilizations(), ...world.nodes, ...world.routes].filter((item) => `${item.label} ${item.summary}`.toLowerCase().includes(q.toLowerCase())).map((item) => ({ id: item.id, kind: item.kind, slug: item.slug, title: item.label, summary: item.summary, aliases: [] })); result = { items: items.slice((page - 1) * 12, page * 12), total: items.length }; }
  const hrefFor = (item: typeof result.items[number]) => item.kind === 'civilization' ? `/civilizations/${item.slug}` : item.kind === 'node' ? `/places/${item.slug}` : `/atlas?y=117&sel=${item.id}`;
  return <SiteShell title="Search" subtitle="Server-backed catalog search">
    <form className="atlas-panel grid gap-3 rounded-[24px] p-5 md:grid-cols-4">
      <input className="rounded-xl bg-white/10 p-3 md:col-span-2" name="q" defaultValue={q} placeholder="Names, aliases, transliterations…" />
      <input className="rounded-xl bg-white/10 p-3" name="region" defaultValue={String(input.region ?? '')} placeholder="Region" />
      <input className="rounded-xl bg-white/10 p-3" name="topic" defaultValue={String(input.topic ?? '')} placeholder="Topic" />
      <input className="rounded-xl bg-white/10 p-3" name="start_year" type="number" defaultValue={String(input.start_year ?? '')} placeholder="From year" />
      <input className="rounded-xl bg-white/10 p-3" name="end_year" type="number" defaultValue={String(input.end_year ?? '')} placeholder="To year" />
      <select className="rounded-xl bg-slate-900 p-3" name="polity_type" defaultValue={String(input.polity_type ?? '')}><option value="">Any polity type</option><option>empire</option><option>kingdom</option><option>dynasty</option><option>civilization</option></select>
      <select className="rounded-xl bg-slate-900 p-3" name="confidence" defaultValue={String(input.confidence ?? '')}><option value="">Any confidence</option><option>high</option><option>medium_high</option><option>medium</option><option>low</option></select>
      <select className="rounded-xl bg-slate-900 p-3" name="review_status" defaultValue={String(input.review_status ?? '')}><option value="">Any review status</option><option>reviewed</option><option>seeded</option><option>needs_review</option><option>placeholder</option></select>
      <select className="rounded-xl bg-slate-900 p-3" name="sort" defaultValue={sort}><option value="relevance">Relevance</option><option value="title">Title</option><option value="date">Date</option></select>
      <button className="rounded-xl bg-cyan-200 p-3 font-semibold text-slate-950">Search</button>
    </form>
    <p className="my-5 text-sm text-[--muted]">{result.total} matching records · page {page}</p>
    <section className="grid gap-4 md:grid-cols-2">{result.items.map((item) => <article className="atlas-panel rounded-[24px] p-5" key={`${item.kind}-${item.id}`}><p className="atlas-kicker">{item.kind}</p><h2 className="mt-2 text-xl font-semibold"><Link href={hrefFor(item)}>{item.title}</Link></h2><p className="mt-3 text-sm leading-6">{item.summary}</p>{item.aliases.length ? <p className="mt-3 text-xs text-[--muted]">Also: {item.aliases.join(' · ')}</p> : null}</article>)}</section>
    <nav className="mt-6 flex gap-3">{page > 1 ? <Link className="underline" href={`?${new URLSearchParams({ ...Object.fromEntries(query), page: String(page - 1) })}`}>Previous</Link> : null}{page * 12 < result.total ? <Link className="underline" href={`?${new URLSearchParams({ ...Object.fromEntries(query), page: String(page + 1) })}`}>Next</Link> : null}</nav>
  </SiteShell>;
}
