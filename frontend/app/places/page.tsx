import Link from 'next/link';
import { SiteShell } from '../../components/atlas/SiteShell';
import { atlasHref, fetchPlaces, featureBadgeTone, formatYear } from '../../lib/atlas';

export default async function PlacesPage() {
  const places = await fetchPlaces();

  return (
    <SiteShell
      title="Places"
      subtitle="Major capitals, ports, and trade hubs that become visible as the user moves from imperial scale into regional scale."
    >
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {places.map((place) => (
          <article className="atlas-panel rounded-[24px] p-5" key={place.id}>
            <p className="text-xs uppercase tracking-[0.18em] text-[--muted]">
              {place.nodeKind.replace('_', ' ')}
            </p>
            <h2 className="mt-2 font-serif text-3xl">{place.label}</h2>
            <p className="mt-2 text-sm text-[--muted]">
              {formatYear(place.startYear)} to {formatYear(place.endYear)}
            </p>
            <p className="mt-3 text-sm leading-6">{place.summary}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {place.statusBadges.map((badge) => (
                <span className={`rounded-full px-2.5 py-1 text-xs ${featureBadgeTone(badge)}`} key={badge}>
                  {badge}
                </span>
              ))}
            </div>
            <div className="mt-4 flex items-center justify-between text-sm">
              <span className="text-[--muted]">
                {place.role.replace('_', ' ')} · {place.coordinates[1].toFixed(2)}, {place.coordinates[0].toFixed(2)}
              </span>
              <div className="flex gap-3"><Link className="text-slate-900 underline" href={`/places/${place.slug}`}>Details</Link>
              <Link className="text-slate-900 underline" href={atlasHref(place)}>
                Open atlas
              </Link></div>
            </div>
          </article>
        ))}
      </section>
    </SiteShell>
  );
}
