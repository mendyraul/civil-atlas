# Private editorial review

The backend serves the review queue at `/editor`. This screen is separate from
the public Next.js frontend and is disabled by default.

## Run it

Use the existing backend environment, migrations and database. Set
`EDITORIAL_API_KEY` through your backend secret store, then enable the editor:

```bash
cd backend
export EDITOR_UI_ENABLED=true
uvicorn app.main:app --host 127.0.0.1 --port 8017
```

Open `http://127.0.0.1:8017/editor`. Enter your reviewer label and the backend's
editorial key. The key is required even in development; it is never put in a
frontend environment variable, URL, cookie, local storage or session storage.
The browser receives a signed, HttpOnly, SameSite=Strict session scoped to
`/editor`. It expires after two hours. Rotating the key invalidates sessions.
Reviewer labels are audit attribution under a shared key, not verified identities.

For a deployed backend, use HTTPS and private ingress (VPN or an authenticated
proxy). Restrict `/editor` and `/editor/*` at ingress alongside both existing
editorial API aliases (`/api/v1/review-*` and `/api/review-*`, plus operational
import/storage endpoints). Configure the proxy to preserve the original scheme
and host: browser writes require an exact same-origin match and a session CSRF
token. Cross-origin editor reads are rejected too; the public frontend's CORS
permissions do not grant access to review data. The screen is not linked or
bundled into the public frontend.

## Review a record

1. Filter the queue by status, entity type, confidence or source. Search matches
   record titles and identifiers. The queue is paginated and starts at needs_review.
2. Open a record. Read its date range, citation, original payload and import notes.
   Boundaries are drawn directly from the supplied Polygon/MultiPolygon geometry,
   including holes, on matching longitude/latitude grids. No external map service
   receives the private geometry. Both views share an extent and zoom controls.
3. Compare with a published primary reading for the same civilization and layer
   type whose dates overlap. If several qualify, choose one explicitly. Missing
   geometry or a missing published primary is shown as missing, not invented.
4. Choose approve, reject, dispute or request changes. Add a rationale, check the
   confirmation and save. History records the reviewer, action, rationale and time.

**Approve publishes immediately**, matching `/api/v1/review-actions` semantics.
Reject, dispute and request changes remove the target from public results.
Approving a boundary does not approve its linked citations automatically. Review
those separately. Placeholder boundaries and source-withdrawn records cannot be
approved through this screen. Source validation flags do not confer historical
approval.

The editor calls the same review-action service as the canonical API. The API
also accepts `dispute`, setting the target status to disputed. Existing API-key
clients remain supported. Editor requests include a version digest of the target
and assignment; a concurrent edit returns 409 and requires a refresh. Target,
assignment, decision and revision writes share a database transaction.

## Citation batches

A selectable batch record must be a source/citation record with **low assignment
priority, high confidence, needs_review status, a nonempty citation and no import
block**. Geometry, places, civilizations and historical claims require individual
review. These rules narrow the batch; they do not replace the editor's judgment.

Select up to 20 eligible records, give a shared rationale and confirm that every
citation was checked. The backend rechecks eligibility and versions under row
locks. The entire batch commits or rolls back; it cannot partially publish.
Every approved record gets its own decision and revision.

## Tests

Against a disposable migrated and seeded PostGIS database:

```bash
pip install -r requirements-editor-tests.txt
pytest -q
python -m playwright install chromium
RUN_EDITOR_BROWSER=1 pytest tests/test_editor_browser.py -q
```

Tests use synthetic records in rolled-back transactions. They cover anonymous
access, CSRF/origin checks, key rotation, expiry, source and placeholder guards,
audit history, stale edits, bulk rollback, public visibility and mobile layout.
They do not approve historical data or change the public site's demo setting.
