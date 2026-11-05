# Data issue delivery

Implementation order: #57, #58, #59, #60, #61. Home-lab rollout (#55) and S3
integration (#62) are deferred. #63 is already completed on main.

## #57 — civilization inventory

Seed 1.2.0 adds 21 source-reported polities with cited claims, original dated
geometry and review assignments. All remain private, including with `--publish`.
The inventory accounts for all 28 prior omissions; seven identity/chronology
cases remain unresolved. Issue #57 cannot be closed until those and editorial
review are resolved. Unchanged seed replay uses a transactional receipt to
preserve subsequent editorial decisions.

Verification: seed dry-run and 30 focused unit/integration tests pass against
PostGIS 16/3.5, including private publication state and review-preserving replay.

No historical records were approved and public demo/deployment settings are unchanged.
