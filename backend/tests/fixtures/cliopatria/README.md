# Cliopatria sample

`sample-117.geojson` contains five unmodified rows copied from
`cliopatria_polities_only_v021.geojson` in the
[Cliopatria repository](https://github.com/Seshat-Global-History-Databank/cliopatria)
(release file dated 2026-10-03, retrieved 2026-10-22). Rows were selected, not
edited. Geometry, years and properties are exactly as published:

- Kingdom of Axum (-50 to 237), Kingdom of Kush (-630 to 337) and Satavahana Dynasty
  (106 to 126): active in 117 CE and mapped to world117 civilizations.
- Satavahana Dynasty (-27 to 105): an earlier row, not active in 117 CE.
- Funan (51 to 237): active in 117 CE but not mapped to a Civil Atlas civilization.

Source: Cliopatria, Seshat Global History Databank. Bennett, J. S. et al.,
*Scientific Data* 12, 247 (2025), https://doi.org/10.1038/s41597-025-04516-9.
Reused under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).

`kushan-117.geojson` is a separate minimal adapter fixture reconstructed from
the existing lossless `frontend/data/history/century-100.json` geometry and its
catalog's Q25979 row for 117–126 CE. Coordinates are unchanged. Unlike the
five-row sample, it does not preserve every original property or the original
release bytes. Its provenance records the upstream archive hash and the local
source path. It has the same Cliopatria CC BY 4.0 attribution. Importing it
still produces unpublished `needs_review` records.
