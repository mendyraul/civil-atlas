# Launch preparation acceptance

## Frontend licensing (#64)

The current source already includes the AGPL package license, repository/source
link, data/source-license page, visible Cliopatria map attribution, and
per-boundary controls. `boundaryChoices` in `AtlasClient.tsx` persists reading
choices in the URL; `visibleBoundaryLayers` in `lib/research.ts` prioritizes
reviewed non-placeholder layers and respects explicit choices. These controls
do not publish records or imply an editorial decision. Existing frontend unit
and browser checks cover source-page notices, attribution and research controls.

The source changes are present. Final live acceptance still needs real reviewed
variants published through the database-backed deployment; keep that operational
check explicit when reconciling the issue.

## Kushan (#57)

World117 version 1.1.0 adds the civilization, a citation-backed existence claim,
the Q25979 crosswalk and the unchanged dated Cliopatria geometry. All new atlas
records are `needs_review`. Dynasty bounds and capital scope are provisional;
source geometry is one interpretation, not an exact frontier. Publishing the
seed must not bypass editorial review. Choose subsequent polities from the
omissions report as a separate reviewed batch.

## Split-host deployment (#66 / #55)

Use [home-lab.md](home-lab.md) and `docker-compose.api.yml` for the separate
Postgres LXC, object-store and API VM layout. Compose validation establishes a
valid application definition, not working hosts. The deployment remains gated
on real endpoints/access, maintained storage selection, saved imports/review,
off-host backups and an exercised restore. Keep public demo mode enabled until
those checks pass.
