import Link from 'next/link';
import { atlasHref, entityAliases, formatYear } from '../../lib/atlas';
import type { AtlasFeature, WorldPayload } from '../../types/atlas';

export function EntityDetail({ entity, world }: { entity: AtlasFeature; world: WorldPayload }) {
  const civilizations = entity.kind === 'civilization' ? [entity.id] : entity.kind === 'node' ? [entity.civilizationId].filter(Boolean) : entity.civilizationIds;
  const places = world.nodes.filter((place) => civilizations.includes(place.civilizationId) || (entity.kind === 'route' && [entity.sourceNodeId, entity.targetNodeId].includes(place.id)));
  const routes = world.routes.filter((route) => civilizations.some((id) => id && route.civilizationIds.includes(id)) || (entity.kind === 'node' && [route.sourceNodeId, route.targetNodeId].includes(entity.id)));
  const events = world.events.filter((event) => event.civilizationIds.some((id) => civilizations.includes(id)) || event.placeIds.includes(entity.id));
  return <article className="atlas-panel rounded-[28px] p-6">
    <p className="atlas-kicker">{entity.kind} · {formatYear(entity.startYear)} to {formatYear(entity.endYear)}</p>
    <h1 className="mt-3 font-serif text-4xl">{entity.kind === 'civilization' ? entity.displayName : entity.label}</h1>
    <p className="mt-4 max-w-3xl leading-7">{entity.summary}</p>
    <p className="mt-4 text-sm text-[--muted]"><strong>Aliases and transliterations:</strong> {(entityAliases[entity.id] ?? [entity.label]).join(' · ')}</p>
    <Link className="mt-5 inline-block rounded-full bg-amber-200 px-4 py-2 text-sm text-slate-950" href={atlasHref(entity)}>View this entity on the atlas</Link>
    <div className="mt-8 grid gap-6 md:grid-cols-2">
      <section><h2 className="text-xl font-semibold">Connected places & routes</h2><ul className="mt-3 space-y-2">{places.map((place) => <li key={place.id}><Link className="underline" href={`/places/${place.slug}`}>{place.label}</Link></li>)}{routes.map((route) => <li key={route.id}><Link className="underline" href={atlasHref(route)}>{route.label}</Link></li>)}</ul></section>
      <section><h2 className="text-xl font-semibold">Events, claims & sources</h2><ul className="mt-3 space-y-2">{events.map((event) => <li key={event.id}>{event.displayDate}: {event.label}</li>)}{entity.evidence.map((source) => <li key={source.id}><Link className="underline" href={`/sources/${source.id}`}>{source.title}</Link></li>)}</ul></section>
    </div>
  </article>;
}
