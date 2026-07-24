import { StatusBadge } from '../badges/StatusBadge';
import { confidenceLabel, evidenceTone, featureBadgeTone, formatYear, reviewLabel, reviewTone } from '../../lib/atlas';
import type { AtlasFeature, AtlasNode, AtlasRoute, Civilization, WorldPayload } from '../../types/atlas';

type DetailPanelProps = {
  feature?: AtlasFeature;
  isFilteredOut?: boolean;
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

function metaRows(feature: AtlasFeature, world: WorldPayload) {
  const relatedEvents = world.events.filter((event) => {
    if (isCivilization(feature)) {
      return event.civilizationIds.includes(feature.id);
    }
    if (isNode(feature)) {
      return event.placeIds.includes(feature.id) || (feature.civilizationId ? event.civilizationIds.includes(feature.civilizationId) : false);
    }
    return event.placeIds.includes(feature.sourceNodeId) || event.placeIds.includes(feature.targetNodeId);
  });

  if (isCivilization(feature)) {
    return [
      ['Type', feature.civilizationType],
      ['Capital', feature.capital],
      ['Confidence', confidenceLabel(feature.confidence)],
      ['Review', reviewLabel(feature.reviewStatus)],
      ['Sources', `${feature.evidence.length}`],
      ['Events', `${relatedEvents.length}`],
      ['Boundary', 'Approximate'],
    ];
  }

  if (isNode(feature)) {
    const owner = feature.civilizationId
      ? world.civilizations.find((civilization) => civilization.id === feature.civilizationId)
      : undefined;

    return [
      ['Type', feature.placeType.replace('_', ' ')],
      ['Role', feature.role.replace('_', ' ')],
      ['Civilization', owner?.displayName ?? 'Unassigned'],
      ['Confidence', confidenceLabel(feature.confidence)],
      ['Review', reviewLabel(feature.reviewStatus)],
      ['Sources', `${feature.evidence.length}`],
      ['Events', `${relatedEvents.length}`],
    ];
  }

  return [
    ['Type', feature.routeKind.replace('_', ' ')],
    ['From', world.nodes.find((node) => node.id === feature.sourceNodeId)?.label ?? 'Unknown'],
    ['To', world.nodes.find((node) => node.id === feature.targetNodeId)?.label ?? 'Unknown'],
    ['Confidence', confidenceLabel(feature.confidence)],
    ['Review', reviewLabel(feature.reviewStatus)],
    ['Sources', `${feature.evidence.length}`],
    ['Events', `${relatedEvents.length}`],
  ];
}

export function DetailPanel({ feature, isFilteredOut = false, world }: DetailPanelProps) {
  if (!feature) {
    return (
      <aside className="atlas-panel flex h-full flex-col rounded-[28px] p-5">
        <p className="atlas-kicker">Selected details</p>
        <h2 className="mt-3 text-2xl font-semibold text-white">No selection yet</h2>
        <p className="mt-4 text-sm leading-7 text-slate-300">
          Click a civilization, place, or route to inspect its date range, confidence, review
          status, and evidence trail.
        </p>
        <div className="mt-5 rounded-[24px] border border-white/10 bg-black/15 p-4 text-sm leading-7 text-slate-300">
          Civil Atlas stays honest when each visual object can explain what it is, when it applies,
          and how certain the current geometry or interpretation really is.
        </div>
      </aside>
    );
  }

  const title = isCivilization(feature) ? feature.displayName : feature.label;
  const description = isCivilization(feature) ? feature.panelDescription : feature.summary;
  const relatedEvents = world.events.filter((event) => {
    if (isCivilization(feature)) {
      return event.civilizationIds.includes(feature.id);
    }
    if (isNode(feature)) {
      return event.placeIds.includes(feature.id) || (feature.civilizationId ? event.civilizationIds.includes(feature.civilizationId) : false);
    }
    return event.placeIds.includes(feature.sourceNodeId) || event.placeIds.includes(feature.targetNodeId);
  });

  return (
    <aside className="atlas-panel flex h-full flex-col rounded-[28px] p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="atlas-kicker">Selected details</p>
          <h2 className="mt-3 text-2xl font-semibold text-white">{title}</h2>
          <p className="mt-2 text-sm text-slate-400">
            {formatYear(feature.startYear)} to {formatYear(feature.endYear)}
          </p>
        </div>
        <div className="rounded-full border border-white/10 bg-white/6 px-3 py-1 text-xs uppercase tracking-[0.18em] text-slate-300">
          {feature.kind}
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {feature.statusBadges.map((badge) => (
          <StatusBadge key={badge} label={badge} tone={featureBadgeTone(badge)} />
        ))}
        <span className={`rounded-full px-2.5 py-1 text-xs ${evidenceTone(feature.confidence)}`}>
          {confidenceLabel(feature.confidence)}
        </span>
        <StatusBadge label={reviewLabel(feature.reviewStatus)} tone={reviewTone(feature.reviewStatus)} />
        {isFilteredOut ? (
          <StatusBadge label="Filtered from map" tone="bg-slate-700 text-slate-100" />
        ) : null}
      </div>

      <p className="mt-5 text-sm leading-7 text-slate-200">{description}</p>

      {isCivilization(feature) ? (
        <div className="mt-5 rounded-[22px] border border-amber-300/20 bg-amber-400/10 px-4 py-4 text-sm leading-7 text-amber-100">
          {feature.extentNote}
        </div>
      ) : null}

      <div className="mt-5 grid grid-cols-2 gap-3">
        {metaRows(feature, world).map(([label, value]) => (
          <div className="rounded-[20px] border border-white/8 bg-black/12 px-4 py-3" key={label}>
            <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">{label}</p>
            <p className="mt-2 text-sm font-medium text-white">{value}</p>
          </div>
        ))}
      </div>

      <section className="mt-6 flex min-h-0 flex-1 flex-col">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-300">Evidence trail</h3>
          <span className="text-xs text-slate-500">{feature.evidence.length} records</span>
        </div>
        <div className="mt-4 flex min-h-0 flex-1 flex-col gap-3 overflow-auto pr-1">
          {feature.evidence.map((record) => (
            <article
              className="rounded-[22px] border border-white/8 bg-black/14 px-4 py-4"
              key={record.id}
            >
              <div className="flex items-start justify-between gap-3">
                <h4 className="font-medium text-white">{record.title}</h4>
                <span className={`rounded-full px-2.5 py-1 text-xs ${evidenceTone(record.confidence)}`}>
                  {confidenceLabel(record.confidence)}
                </span>
              </div>
              <p className="mt-2 text-xs uppercase tracking-[0.16em] text-slate-500">
                {record.citation}
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <StatusBadge label={reviewLabel(record.reviewStatus)} tone={reviewTone(record.reviewStatus)} />
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-300">{record.notes}</p>
            </article>
          ))}
        </div>
      </section>

      {relatedEvents.length > 0 ? (
        <section className="mt-6">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-300">
              Historical log
            </h3>
            <span className="text-xs text-slate-500">{relatedEvents.length} related events</span>
          </div>
          <div className="mt-4 flex flex-col gap-3">
            {relatedEvents.map((event) => (
              <article className="rounded-[22px] border border-white/8 bg-black/14 px-4 py-4" key={event.id}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h4 className="font-medium text-white">{event.label}</h4>
                    <p className="mt-2 text-xs uppercase tracking-[0.16em] text-slate-500">
                      {event.displayDate} · {event.eventType.replace('_', ' ')}
                    </p>
                  </div>
                  <StatusBadge label={reviewLabel(event.reviewStatus)} tone={reviewTone(event.reviewStatus)} />
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-300">{event.summary}</p>
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </aside>
  );
}
