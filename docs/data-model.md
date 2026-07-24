# Data Model

## Core entities

- `civilizations`: canonical polities with time range, description, color,
  confidence, and review state
- `civilization_layers`: map-ready extent or influence layers for a civilization
- `historical_relationships`: first-class ties between civilizations, places,
  and layers such as contested frontiers, trade exchange, or influence overlap
- `places`: canonical historical places with time range and confidence metadata
- `civilization_places`: time-bounded place memberships and roles
- `civilization_edges`: time-bounded routes or connections between places
- `eras`: named interpretive periods that stay active across a year range
- `historical_events`: dated or bounded changes that explain why the map differs
- `sources`: canonical source metadata records
- `historical_claims`: normalized claims such as existence, boundary, location,
  route, or capital-role support
- `evidence_links`: links from sources to specific entities and claim types

## Relationships

- One civilization can have many layers
- One civilization can have many competing or complementary layer variants in a
  shared interpretation group
- One civilization can relate to many places through `civilization_places`
- One civilization can have many edges through `civilization_edges`
- One civilization can participate in many `historical_relationships`
- One era can feature many civilizations and one civilization can appear in many eras
- One historical event can reference many civilizations, places, and sources
- One source can support many entities through `evidence_links`
- One claim can reference many sources and one source can support many claims

## Interpretation variants

- `civilization_layers` now carry:
  - `variant_group`: groups alternative readings of the same entity
  - `interpretation_label`: human explanation of that reading
  - `interpretation_kind`: one of `boundary_variant`, `influence_zone`,
    `contested_zone`, `administrative_layer`, or `thematic_overlay`
  - `is_primary`: marks the default atlas reading without deleting alternatives
- This lets Civil Atlas represent conservative boundaries vs maximal campaign
  reach, direct administration vs corridor influence, and cultural extents vs
  sovereign control without pretending only one geometry is final truth.

## Confidence and review

- Confidence values: `low`, `medium`, `medium_high`, `high`
- Review values: `placeholder`, `seeded`, `needs_review`, `reviewed`
- Every map-facing object should carry both, even when geometry is only a
  placeholder
- Timeline-facing eras and events should also carry source-backed explanation
  text, not just date bounds
