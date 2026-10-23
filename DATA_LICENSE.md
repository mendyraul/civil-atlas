# Data license

The Civil Atlas historical database is made available under the
[Open Database License (ODbL) 1.0](LICENSES/ODbL-1.0.txt).

This covers:

- import manifests and crosswalks under `backend/data/`
- the frontend demo snapshot `frontend/data/demoWorld117.ts`
- database exports and the data served by the public Civil Atlas API

The application code is licensed separately under
[AGPL-3.0-or-later](LICENSE). Documentation is under
[CC BY 4.0](LICENSES/CC-BY-4.0.txt). [`REUSE.toml`](REUSE.toml) maps every path
to its license.

## What ODbL asks of you

You may copy, share, adapt and build on the database, including in your own
projects, as long as you:

1. **Attribute.** Credit "Civil Atlas contributors" and keep the upstream
   credits listed in [ATTRIBUTION.md](ATTRIBUTION.md).
2. **Share alike.** If you publicly use or share an adapted version of the
   database, release that adapted database under the ODbL as well.
3. **Keep it open.** Don't apply technical restrictions, such as DRM, to copies
   you distribute without also offering an unrestricted version.

Maps, images and other "produced works" made from the database may use any
license, but they must carry the attribution above.

## Upstream credits travel with the data

Parts of the database come from sources under CC BY licenses (see
[ATTRIBUTION.md](ATTRIBUTION.md)). Those licenses require credit in every copy
and adaptation. Any produced work or derived database must therefore credit
both Civil Atlas and each upstream source it uses, not only Civil Atlas.
Every record also carries its own source citation through the `sources` and
`source_records` tables.

## What may enter the database

Only sources under CC0, public domain, CC BY 3.0/4.0, or ODbL may be imported.
Non-commercial, no-derivatives, GPL, and CC BY-SA data are not compatible
with this license. Those sources are reference-only. See
[docs/licensing-register.md](docs/licensing-register.md).
