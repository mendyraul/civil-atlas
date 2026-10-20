# Next product increment: ingestion and editorial review

The next increment should improve the evidence pipeline before adding more
historical coverage. New coverage without a review path would increase the
amount of unreviewed geometry and claims faster than the team can audit it.

## Sequence

1. Exercise the local [Pleiades ingestion pilot](pleiades-pilot.md), which provides
   an adapter interface, preserved raw bytes and licenses, repeatable versioned
   imports, and editorial assignments. Live object storage and staging drills
   remain required before expanding coverage.
2. Add an operator import-run screen for manifest preview, validation errors,
   dry runs, retries, and an immutable import audit record.
3. Add an editorial queue backed by `review_assignments`, with claim and
   geometry diffs, evidence links, confidence rationale, and explicit approve,
   request-changes, and reject decisions.
4. Publish only reviewed records by default, while retaining a deliberate
   needs-review view for research and QA.
5. Expand historical coverage only after the pilot import and restore/review
   drills succeed in staging.

## Definition of done

Every visible claim and geometry has a source record, confidence, review status,
and valid time bounds. Every import is repeatable from a versioned manifest and
auditable by dataset version, content hash, actor, and revision history.
