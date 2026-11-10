-- Canonical publication remains in atlas_entities; these are typed projections.
CREATE TABLE IF NOT EXISTS entities (
  id varchar(64) PRIMARY KEY, slug varchar(255) NOT NULL UNIQUE,
  entity_kind varchar(64) NOT NULL, canonical_name varchar(255) NOT NULL,
  valid_from_year integer, valid_to_year integer, review_status varchar(64) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS people (
  entity_id varchar(64) PRIMARY KEY REFERENCES entities(id), birth_year integer, death_year integer
);
CREATE TABLE IF NOT EXISTS offices (
  entity_id varchar(64) PRIMARY KEY REFERENCES entities(id),
  jurisdiction_entity_id varchar(64) REFERENCES entities(id), office_category varchar(64) NOT NULL
);
CREATE TABLE IF NOT EXISTS office_tenures (
  id varchar(64) PRIMARY KEY,
  office_entity_id varchar(64) NOT NULL REFERENCES offices(entity_id),
  person_entity_id varchar(64) NOT NULL REFERENCES people(entity_id),
  valid_from_year integer NOT NULL, valid_to_year integer NOT NULL,
  CHECK (valid_from_year <= valid_to_year)
);
