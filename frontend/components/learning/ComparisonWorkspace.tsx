'use client';

import { useMemo, useState } from 'react';
import { world117 } from '../../data/world117';
import { formatYear } from '../../lib/atlas';

const dimensions = ['Governance', 'Chronology', 'Territory', 'Economy', 'Religion', 'Evidence quality'] as const;

export function ComparisonWorkspace() {
  const [year, setYear] = useState(117);
  const [pinned, setPinned] = useState(['roman-empire', 'han-dynasty']);
  const active = useMemo(() => world117.civilizations.filter((item) => item.startYear <= year && item.endYear >= year), [year]);
  const selected = active.filter((item) => pinned.includes(item.id));
  const value = (id: string, dimension: typeof dimensions[number]) => {
    const item = selected.find((entry) => entry.id === id)!;
    if (dimension === 'Governance') return `${item.civilizationType}; capital: ${item.capital}`;
    if (dimension === 'Chronology') return `${formatYear(item.startYear)}–${formatYear(item.endYear)}`;
    if (dimension === 'Territory') return item.extentNote;
    if (dimension === 'Economy') return item.summary;
    if (dimension === 'Religion') return 'Not asserted in the current reviewed seed; consult linked evidence.';
    return `${item.confidence.replace('_', ' ')} confidence · ${item.reviewStatus.replace('_', ' ')} · ${item.evidence.length} source(s)`;
  };
  const toggle = (id: string) => setPinned((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);

  return <main className="space-y-5" aria-labelledby="compare-title">
    <header className="atlas-hero rounded-[30px] p-6"><p className="atlas-kicker">Comparison workspace</p><h1 id="compare-title" className="mt-2 text-4xl font-semibold">Pin polities at one date</h1><p className="mt-3 max-w-3xl text-slate-300">Compare like with like while keeping uncertainty visible. Select two or more active polities; missing evidence stays missing rather than becoming a guess.</p></header>
    <section className="atlas-panel rounded-[26px] p-5" aria-label="Comparison controls">
      <label className="font-semibold" htmlFor="compare-year">Selected date: {formatYear(year)}</label><input id="compare-year" className="atlas-range mt-3 w-full" type="range" min={-600} max={1800} value={year} onChange={(event) => setYear(Number(event.target.value))} />
      <fieldset className="mt-5"><legend className="font-semibold">Pinned polities ({selected.length}; choose at least 2)</legend><div className="mt-3 flex flex-wrap gap-2">{active.map((item) => <label className="rounded-full border border-white/20 px-4 py-2" key={item.id}><input className="mr-2" type="checkbox" checked={pinned.includes(item.id)} onChange={() => toggle(item.id)} />{item.label}</label>)}</div></fieldset>
    </section>
    {selected.length < 2 ? <p role="status" className="rounded-xl border border-amber-300/50 p-4 text-amber-100">Pin at least two active polities to compare.</p> : <div className="overflow-x-auto rounded-[26px] border border-white/10"><table className="w-full border-collapse text-left"><caption className="p-4 text-left text-slate-300">Narrative and tabular equivalent to the map for {formatYear(year)}. Territory descriptions explicitly preserve uncertainty.</caption><thead><tr><th scope="col" className="p-4">Dimension</th>{selected.map((item) => <th scope="col" className="p-4" key={item.id}>{item.label}</th>)}</tr></thead><tbody>{dimensions.map((dimension) => <tr className="border-t border-white/10" key={dimension}><th scope="row" className="p-4 text-cyan-200">{dimension}</th>{selected.map((item) => <td className="min-w-64 p-4 text-slate-300" key={item.id}>{value(item.id, dimension)}{dimension === 'Evidence quality' && <div className="mt-2">{item.evidence.map((source) => <a className="block text-cyan-300 underline" href={`/sources#${source.id}`} key={source.id}>{source.title}</a>)}</div>}</td>)}</tr>)}</tbody></table></div>}
  </main>;
}
