# Data Model

## Core entities

- `civilizations`: canonical polities with time range, description, color,
  confidence, and review state
- `civilization_layers`: map-ready extent or influence layers for a civilization
- `places`: canonical historical places with time range and confidence metadata
- `civilization_places`: time-bounded place memberships and roles
- `civilization_edges`: time-bounded routes or connections between places
- `sources`: canonical source metadata records
- `historical_claims`: normalized claims such as existence, boundary, location,
  route, or capital-role support
- `evidence_links`: links from sources to specific entities and claim types

## Relationships

- One civilization can have many layers
- One civilization can relate to many places through `civilization_places`
- One civilization can have many edges through `civilization_edges`
- One source can support many entities through `evidence_links`
- One claim can reference many sources and one source can support many claims

## Confidence and review

- Confidence values: `low`, `medium`, `medium_high`, `high`
- Review values: `placeholder`, `seeded`, `needs_review`, `reviewed`
- Every map-facing object should carry both, even when geometry is only a
  placeholder
