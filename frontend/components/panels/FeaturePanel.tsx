import { StatusBadge } from '../badges/StatusBadge';
import { evidenceTone, featureBadgeTone, formatYear, reviewTone } from '../../lib/atlas';
import type { AtlasFeature, AtlasNode, AtlasRoute, Civilization, WorldPayload } from '../../types/atlas';

type FeaturePanelProps = {
  feature?: AtlasFeature;
  world: WorldPayload;
};

function isCivilization(feature: AtlasFeature): feature is Civilization {
  return feature.kind === 'civilization';
}

function isNode(feature: AtlasFeature): feature is AtlasNode {
  return feature.kind === 'node';
}

function isRoute(feature: AtlasFeature): feature is AtlasRoute {
  return feature.kind === 'route';
}

export function FeaturePanel({ feature, world }: FeaturePanelProps) {
  if (!feature) {
    return (
      <aside className="atlas-panel flex flex-col gap-4 rounded-[24px] p-5">
        <p className="text-xs uppercase tracking-[0.18em] text-[--muted]">Selection</p>
        <h2 className="font-serif text-3xl">Pick a layer, city, or route</h2>
        <p className="text-sm leading-6 text-[--muted]">
          Civil Atlas becomes useful when every visual object can explain itself:
          date range, uncertainty, and evidence status.
        </p>
      </aside>
    );
  }

  const owner =
    isNode(feature) && feature.civilizationId
      ? world.civilizations.find((civilization) => civilization.id === feature.civilizationId)
      : undefined;

  return (
    <aside className="atlas-panel flex flex-col gap-4 rounded-[24px] p-5">
      <p className="text-xs uppercase tracking-[0.18em] text-[--muted]">{feature.kind}</p>
      <h2 className="font-serif text-3xl">
        {feature.kind === 'civilization' ? feature.displayName : feature.label}
      </h2>
      <p className="text-sm text-[--muted]">
        Active {formatYear(feature.startYear)} to {formatYear(feature.endYear)}
      </p>

      {isCivilization(feature) ? (
        <>
          <p className="text-sm leading-6">{feature.summary}</p>
          <p className="text-sm leading-6">{feature.panelDescription}</p>
          <div className="flex flex-wrap gap-2">
            {feature.statusBadges.map((badge) => (
              <StatusBadge label={badge} tone={featureBadgeTone(badge)} key={badge} />
            ))}
          </div>
          <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            {feature.extentNote}
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="block text-xs uppercase tracking-wide text-[--muted]">Capital</span>
              <strong>{feature.capital}</strong>
            </div>
            <div>
              <span className="block text-xs uppercase tracking-wide text-[--muted]">Layer type</span>
              <strong>Extent polygon</strong>
            </div>
          </div>
        </>
      ) : null}

      {isNode(feature) ? (
        <>
          <p className="text-sm leading-6">{feature.summary}</p>
          <div className="flex flex-wrap gap-2">
            {feature.statusBadges.map((badge) => (
              <StatusBadge label={badge} tone={featureBadgeTone(badge)} key={badge} />
            ))}
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="block text-xs uppercase tracking-wide text-[--muted]">Node type</span>
              <strong>{feature.nodeKind.replace('_', ' ')}</strong>
            </div>
            <div>
              <span className="block text-xs uppercase tracking-wide text-[--muted]">Associated polity</span>
              <strong>{owner?.label ?? 'Unassigned'}</strong>
            </div>
          </div>
        </>
      ) : null}

      {isRoute(feature) ? (
        <>
          <p className="text-sm leading-6">{feature.summary}</p>
          <div className="flex flex-wrap gap-2">
            {feature.statusBadges.map((badge) => (
              <StatusBadge label={badge} tone={featureBadgeTone(badge)} key={badge} />
            ))}
          </div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="block text-xs uppercase tracking-wide text-[--muted]">Route class</span>
              <strong>{feature.routeKind}</strong>
            </div>
            <div>
              <span className="block text-xs uppercase tracking-wide text-[--muted]">Connected polities</span>
              <strong>{feature.civilizationIds.length}</strong>
            </div>
          </div>
        </>
      ) : null}

      <section className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">Evidence</h3>
          <span className="text-sm text-[--muted]">{feature.evidence.length} records</span>
        </div>
        {feature.evidence.map((record) => (
          <article key={record.id} className="border-t border-slate-200 pt-3">
            <h4 className="font-semibold">{record.title}</h4>
            <p className="mt-1 text-sm text-[--muted]">{record.citation}</p>
            <div className="mt-2 flex flex-wrap gap-2">
              <span className={`rounded-full px-2.5 py-1 text-xs ${evidenceTone(record.confidence)}`}>
                {record.confidence} confidence
              </span>
              <StatusBadge
                label={record.reviewStatus.replace('_', ' ')}
                tone={reviewTone(record.reviewStatus)}
              />
            </div>
            <p className="mt-2 text-sm leading-6">{record.notes}</p>
          </article>
        ))}
      </section>
    </aside>
  );
}
