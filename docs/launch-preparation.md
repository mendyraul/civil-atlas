# Launch preparation acceptance

## Frontend licensing (#64)

The current source already includes the AGPL package license, repository/source
link, data/source-license page, visible Cliopatria map attribution, and
per-boundary controls. `boundaryChoices` in `AtlasClient.tsx` persists reading
choices in the URL; `visibleBoundaryLayers` in `lib/research.ts` prioritizes
reviewed non-placeholder layers and respects explicit choices. These controls
do not publish records or imply an editorial decision. Existing frontend unit
and browser checks cover source-page notices, attribution and research controls.

The remaining automated acceptance uses the shared synthetic fixture in
`frontend/acceptance/fixtures/boundary-readings.json`. The backend test first
keeps its records private, then approves two readings through the editorial API
and checks the exact published contract. A third reading stays unpublished.
The non-demo browser suite consumes that contract and checks primary versus
alternative visibility, hiding both, shared URL reloads, source links, and
Cliopatria credit appearing/disappearing with the visible layer. Run it with
`npm run test:licensing`; CI runs it after the normal and failed-basemap suites.
These fixtures test mechanics, never historical accuracy or a second real source.
Run browser suites sequentially with the frontend development server stopped;
the non-demo acceptance suite owns port 3102 and serves only a test API contract.
It never sends the editorial key to a browser or publishes production records.
CI also runs the normal browser suite with one worker. A parallel run exhausted
the unchanged 30-second scenario budget while notes and linked maps shared the
runner; serial execution avoids that resource contention without adding retries.
Linked maps also tag programmatic camera events, so an older follower animation
cannot become a new user command. A deterministic unit regression and repeated
browser checks cover interrupted camera movement.

The normal source-page acceptance also checks the AGPL package declaration,
source link, three license links, ODbL/upstream-credit notice and all current
included/planned attribution entries. This establishes the UI acceptance for
#64. Actual publication of another researched border reading is still #58's
data work and #55's live rollout; do not fabricate one to check off the UI issue.

Comparison cameras also retain the source pane's latest view and suppress the
old intermediate event emitted when stopping a follower animation. The browser
regression issues a second zoom before the follower settles and checks that
both panes reach the new target while their dates remain independent.

## Kushan (#57)

World117 version 1.1.0 adds the civilization, a citation-backed existence claim,
the Q25979 crosswalk and the unchanged dated Cliopatria geometry. All new atlas
records are `needs_review`. Dynasty bounds and capital scope are provisional;
source geometry is one interpretation, not an exact frontier. Publishing the
seed must not bypass editorial review. Choose subsequent polities from the
omissions report as a separate reviewed batch.

The crosswalk now retains the expected source name, so an unrelated polity
sharing a QID cannot attach its geometry to Kushan or another mapped entity.
Repeatable seed publication is tested explicitly: it creates no duplicate
records, does not withdraw existing public Rome data, and leaves the new
Kushan entity, claim and layer private.

## Split-host deployment (#66 / #55)

Use [home-lab.md](home-lab.md) and `docker-compose.api.yml` for the separate
Postgres LXC, object-store and API VM layout. Compose validation establishes a
valid application definition, not working hosts. The deployment remains gated
on real endpoints/access, maintained storage selection, saved imports/review,
off-host backups and an exercised restore. Keep public demo mode enabled until
those checks pass and the reviewed API preserves the current 38-polity timeline
and sourced geometry. A 117 CE-only API is not a replacement for the expanded
public preview. The home-lab guide lists the exact operator inputs still needed.

## Delivery and issue accounting

- #70 merged the focused Zod 4.4.3 → 4.6.7 lockfile fix for #65. The audit gate
  passes. The first main run then exposed the existing linked-camera bug;
  #71 includes its fix and the interrupted-animation regression.
- #71 merged the bounded Kushan seed and provider-neutral home-lab guide.
  Kushan is the first slice of #57, not completion of all missing polities.
- Main's [post-merge CI](https://github.com/mendyraul/civil-atlas/actions/runs/40574694237)
  passes frontend, backend, licensing and deployment-configuration checks.
- The follow-up acceptance change completes the source-identity guard and #64
  UI checks without rewriting the prepared PRs or changing public demo mode.
- Reconcile #64 and #66 only against merged acceptance evidence. Keep #55,
  the remainder of #57 and subsequent import/storage/editorial/release issues
  open; #67 summarizes that evidence rather than duplicating implementation.

## Isolated verification — October 27, 2026

- Clean `npm ci` and `npm audit --audit-level=high`: zero findings. Typecheck,
  lint, 38 frontend unit tests and the production build pass.
- The full backend suite passes 80 tests against a disposable PostgreSQL
  16/PostGIS 3.5 database, with optional MCP dependencies installed.
- Browser acceptance passes 16 normal scenarios, the separate basemap failure
  case and the non-demo published-reading case. Desktop, mobile and later-year
  map views retain the source geometry and modern-border style.
- A dry run of the unchanged archived Cliopatria v0.2.1 release produces eight
  mapped 117 CE layers and 28 omissions, with no import publication.
- The logical backup/restore commands were exercised into a second disposable
  database. All 345 operational records and 158 public records matched the test
  source database. These are observed test counts, not a production invariant.
- A staging-mode API against the restored database returned 200 for liveness,
  readiness, data version and world/117. Unauthenticated editorial access
  returned 401, and unreviewed Kushan remained absent from the public world.
- Compose configuration and REUSE coverage pass. No live Proxmox host, real S3
  provider, tunnel, off-host backup destination or production restore was tested.

Exact candidate/main CI links belong in the delivery PR and issue acceptance
record. Local rehearsal is not evidence that #55's host rollout is complete.

## Separate dependency follow-up

GitHub also reports the moderate pytest temporary-directory advisory
GHSA-6w46-j5rx-g56g against the backend requirements and the MCP requirements
include. Both alerts refer to the same test-runner dependency; the patched
version is 9.0.3. Dependabot PR #72 already proposes that major-version update.
Keep its compatibility review separate from the narrow frontend fix. A clean
`npm audit` does not establish that Python dependencies have no advisories.
