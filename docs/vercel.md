# Vercel deployment

Vercel hosts only the Next.js frontend. The FastAPI service, PostgreSQL
database, and object storage must be deployed separately and the frontend must
be given the public HTTPS URL of that API.

When `NEXT_PUBLIC_DEMO_MODE=true`, the static preview uses the original
Cliopatria v0.2.1 borders bundled in `frontend/data/cliopatria117.json`, with
their source citations, low confidence and inclusive validity intervals.
It does not fall back to schematic borders outside those intervals. Other
demo records and guided narratives remain illustrative; spatial research
still requires a deployed API. See [attribution](../ATTRIBUTION.md).

## GitHub identity

Deployments are associated with the author of the pushed commit. The repository
remote is `mendyraul/civil-atlas`, and new commits must use the exact private
GitHub noreply address shown in the `mendyraul` account settings. The old work
address `rmendy@biznesshosting.com` is not a GitHub identity for this project.

The rejected commit can remain in history. Push a new corrective commit after
the local author configuration is fixed; do not force-push shared `main`.

## Project settings

The preferred Vercel Project Root Directory is `frontend`. The repository also
contains a root `vercel.json` so a project configured at the repository root
uses the same frontend build.

Set these build-time environment variables in Vercel for Preview and
Production:

```text
NEXT_PUBLIC_API_BASE_URL=https://<public-api-host>
NEXT_PUBLIC_DEMO_MODE=false
NEXT_PUBLIC_MAP_STYLE_URL=/map-styles/minimal.json
```

`NEXT_PUBLIC_API_BASE_URL` must be an HTTPS origin, without a trailing slash.
The build fails with a direct message when Vercel is in non-demo mode without
this value. Never put database credentials or S3 secrets in Vercel; they belong
to the backend deployment's secret store. `EDITORIAL_API_KEY` is also a
backend-only secret; use it from the future internal editorial client through
the `X-Editorial-Key` header and never expose it as a `NEXT_PUBLIC_*` value.

## Release checks

1. Confirm the backend `/health/ready` endpoint is reachable from the browser.
2. Add the Vercel origin to backend `CORS_ORIGINS`.
3. Import and explicitly publish the validated manifest in staging.
4. Verify the atlas, search, sources, and health endpoints from the deployed UI.
5. Promote the same reviewed dataset and configuration to production.
