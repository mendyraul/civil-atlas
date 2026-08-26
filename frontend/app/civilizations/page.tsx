import Link from 'next/link';
import { SiteShell } from '../../components/atlas/SiteShell';
import { atlasHref, fetchCivilizations, featureBadgeTone, formatYear } from '../../lib/atlas';

export default async function CivilizationsPage() {
  const civilizations = await fetchCivilizations();

  return (
    <SiteShell
      title="Civilizations"
      subtitle="Seed polities spanning roughly 600 BCE to 1800 CE, each with a stable visual identity and explicit uncertainty cues."
    >
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {civilizations.map((civilization) => (
          <article className="atlas-panel rounded-[24px] p-5" key={civilization.id}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.18em] text-[--muted]">
                  {formatYear(civilization.startYear)} to {formatYear(civilization.endYear)}
                </p>
                <h2 className="mt-2 font-serif text-3xl">{civilization.displayName}</h2>
              </div>
              <span
                className="mt-2 inline-block h-4 w-4 rounded-full"
                style={{ backgroundColor: civilization.color }}
              />
            </div>
            <p className="mt-3 text-sm leading-6">{civilization.shortDescription}</p>
            <p className="mt-3 text-sm text-[--muted]">{civilization.extentNote}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {civilization.statusBadges.map((badge) => (
                <span className={`rounded-full px-2.5 py-1 text-xs ${featureBadgeTone(badge)}`} key={badge}>
                  {badge}
                </span>
              ))}
            </div>
            <div className="mt-4 flex items-center justify-between text-sm">
              <span className="text-[--muted]">
                {civilization.civilizationType} · capital: {civilization.capital}
              </span>
              <div className="flex gap-3"><Link className="text-slate-900 underline" href={`/civilizations/${civilization.slug}`}>Details</Link>
              <Link className="text-slate-900 underline" href={atlasHref(civilization)}>
                View on atlas
              </Link></div>
            </div>
          </article>
        ))}
      </section>
    </SiteShell>
  );
}
