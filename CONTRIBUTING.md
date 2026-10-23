# Contributing to Civil Atlas

Thanks for helping build an open atlas of world history.

## Licensing of contributions

Contributions are accepted under the same license as the files they change
(inbound = outbound). [`REUSE.toml`](REUSE.toml) maps every path to its license:

| Area | License |
|---|---|
| Code and configuration | [AGPL-3.0-or-later](LICENSE) |
| Historical data (`backend/data/`, demo snapshot) | [ODbL 1.0](DATA_LICENSE.md) |
| Documentation (`docs/`, top-level `.md` files) | [CC BY 4.0](LICENSES/CC-BY-4.0.txt) |

By opening a pull request you confirm that you have the right to submit the
work under these licenses.

## Adding a data source

Historical data is only useful if it can be shared openly, so new sources are
gated:

1. Add a row to [`docs/licensing-register.md`](docs/licensing-register.md)
   with the source's license, as stated in the source's own LICENSE file or
   terms page. Don't rely on a catalog listing.
2. Only CC0, public domain, CC BY 3.0/4.0, and ODbL sources may be imported.
   Non-commercial (NC), no-derivatives (ND), GPL, and CC BY-SA data are
   **reference-only**, even though Civil Atlas is non-commercial, because they
   cannot be redistributed under the ODbL.
3. Add the credit line to [`ATTRIBUTION.md`](ATTRIBUTION.md).
4. Imports go through `backend/app/ingestion/` and land as `needs_review`.
   The importer refuses licenses outside the allowlist in
   `backend/app/ingestion/licenses.py`.

Never paste data copied from copyrighted atlases, books, or commercial
datasets such as Euratlas or Centennia. Cite them as evidence instead.
