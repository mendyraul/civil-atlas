# Coverage roadmap and region packs

Coverage grows through versioned region/era packs rather than edits scattered
through application code. The registry is
`backend/data/imports/coverage/v1/manifest.json` and is visible to operators and
loading clients at `/api/v1/coverage/packs`.

## Directional rollout

1. **Foundation:** maintain the 117 CE cross-region comparison with western
   Mediterranean/Europe and eastern Han corridors as the first world view.
2. **Southward depth:** review the Nile–Red Sea and South Asian packs, then add
   more cities and routes at regional/local zoom.
3. **Eastward depth:** extend the Near East, Iranian plateau, Central Asian, and
   Silk Road packs while preserving competing boundary variants.
4. **Westward breadth:** expand Mesoamerican and later American packs only when
   each new record has a source, license, confidence, review state, and valid
   time bounds.

Each pack declares its era IDs, focal years, maturity, coverage tier, review
status, source policy, and zoom loading strategy. `foundation` means the pack
anchors the current world view; `pilot` means it is suitable for a bounded
review/import cycle; `planned` means its shape is agreed but records are not
ready for public release. `region_seed` is never a substitute for reviewed
historical coverage.

## Loading and quality gates

- World zoom loads only foundation summaries and primary layers.
- Regional zoom loads a pack's reviewed places and routes.
- Local zoom loads the full pack geometry and evidence links.
- New records are imported as unpublished until editorial review promotes them.
- A pack cannot move to the next maturity tier without a repeatable import,
  provenance audit, and restore/review drill in staging.

This keeps breadth and depth measurable while allowing the frontend to remain
fast as the number of records grows.
