# Civil Atlas: World at 117 CE

## Why this slice exists

The 117 CE prototype is not trying to solve historical cartography in one go.
It exists to prove the product loop:

1. Choose a year.
2. See active polities and routes.
3. Zoom toward meaningful place nodes.
4. Click any object and inspect evidence, confidence, and review state.

## MVP interaction rules

- Extent layers and route overlays remain visible from low zoom.
- Place nodes appear only after a zoom threshold so the world view does not turn
  into confetti.
- A single selection panel handles civilizations, places, and routes to keep
  the review model consistent across feature types.

## Data model priorities

- Every feature gets a start year and end year.
- Every feature gets evidence records even if the evidence is still provisional.
- Confidence and review status are explicit from day one.
- Routes are first-class objects rather than just decoration.

## Near-term follow-ups

- Replace seed polygons with reviewed GeoJSON boundaries
- Add confidence-aware styling for uncertain borders
- Add filtering by layer type and source review status
- Split direct rule from influence and contested zones
- Expand the seed set west/east/south while keeping the provenance model strict
