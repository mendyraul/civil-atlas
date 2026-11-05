# OpenHistoricalMap Roman boundary at 117 CE

`roman-117.overpass.json.gz` losslessly compresses the exact JSON response to
`[out:json][timeout:30];relation(2849539);out geom;` from
https://overpass-api.openhistoricalmap.org/api/interpreter, retrieved November 5,
2026 at 21:46 UTC. The response declares CC0. Decompressed source SHA-256:
`f1e0015b084a1c91ffffe401f21158637ee5d2efe2eba6bf97788007e8310b30`.

https://www.openhistoricalmap.org/relation/2849539 supplies original ways,
coordinates, tags and its admin-centre node. The relation uses Wikidata Q2277
(Roman Empire); Cliopatria's source Q12544 is not a canonical cross-source ID.
The boundary carries `fixme:s=needs source for boundary lines`, so it remains
private and `needs_review`. This fixture tests import mechanics and does not
establish historical accuracy or publication eligibility.
