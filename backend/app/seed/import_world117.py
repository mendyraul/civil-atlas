"""Transactional, repeatable importer for a versioned atlas manifest.

Run with ``python -m app.seed.import_world117``. Edit the versioned JSON
manifest, increment its dataset version, and rerun the command; no application
code change is required. The complete manifest is validated before a database
transaction can change repository data.
"""

import argparse
from typing import Any

from pydantic import BaseModel

from app.db.session import session_scope
from app.seed import catalog
from app.services import knowledge
from app.services.repository import AtlasRepository, PUBLIC_ENTITY_TYPES

DATASET_ORDER = tuple(catalog.DATASET_MODELS)
AUDITED_DATASETS = {
    "civilizations",
    "layers",
    "nodes",
    "routes",
    "claims",
    "relationships",
}


def _validate_audit_contract(
    datasets: list[tuple[str, list[BaseModel], type[BaseModel]],]
) -> None:
    source_ids = {str(item.id) for item in catalog.DATASETS["source_records"]}
    for kind, records, _ in datasets:
        if kind not in AUDITED_DATASETS:
            continue
        for record in records:
            value = record.model_dump(mode="json")
            missing = [
                field
                for field in ("confidence", "review_status", "source_record_ids")
                if not value.get(field)
            ]
            if kind in {"layers", "claims", "relationships"}:
                missing.extend(
                    field for field in ("valid_from_year", "valid_to_year")
                    if value.get(field) is None
                )
                if kind == "layers" and value.get("geometry_json") is None:
                    missing.append("geometry_json")
            else:
                missing.extend(
                    field for field in ("start_year", "end_year")
                    if value.get(field) is None
                )
            if missing:
                raise ValueError(f"{kind}/{value.get('id')} is missing audit fields: {', '.join(missing)}")
            unknown_sources = set(value["source_record_ids"]) - source_ids
            if unknown_sources:
                raise ValueError(
                    f"{kind}/{value.get('id')} references unknown source records: "
                    f"{', '.join(sorted(unknown_sources))}"
                )


def _validated_records() -> list[tuple[str, list[BaseModel], type[BaseModel]]]:
    validated: list[tuple[str, list[BaseModel], type[BaseModel]]] = []
    for kind in DATASET_ORDER:
        schema = catalog.DATASET_MODELS[kind]
        records = [schema.model_validate(item) for item in catalog.DATASETS[kind]]
        validated.append((kind, records, schema))
    return validated


def import_fixture(
    actor: str = "fixture:world117", dry_run: bool = False, publish: bool = False
) -> dict[str, Any]:
    datasets = _validated_records()
    _validate_audit_contract(datasets)
    counts: dict[str, Any] = {
        "created": 0,
        "updated": 0,
        "duplicate": 0,
        "dataset_slug": catalog.MANIFEST["dataset_slug"],
        "dataset_version": catalog.DATASET_VERSION,
        "manifest_sha256": f"sha256:{catalog.MANIFEST_SHA256}",
        "manifest_path": str(catalog.MANIFEST_PATH),
        "dry_run": dry_run,
        "publish": publish,
    }
    if dry_run:
        counts["records_discovered"] = sum(len(records) for _, records, _ in datasets)
        return counts

    audit_actor = (
        f"{actor};dataset={catalog.MANIFEST['dataset_slug']};"
        f"version={catalog.DATASET_VERSION};manifest_sha256={catalog.MANIFEST_SHA256};"
        f"knowledge_version={knowledge.DATASET_VERSION};knowledge_sha256={knowledge.MANIFEST_SHA256}"
    )
    with session_scope() as session:
        repository = AtlasRepository(session)
        for kind, records, schema in datasets:
            seen: set[str] = set()
            for raw in records:
                record = schema.model_validate(raw).model_dump(mode="json")
                if kind == "sources":
                    record.setdefault("dataset_version", catalog.DATASET_VERSION)
                external_id = str(record.get("slug") or record["id"])
                if external_id in seen:
                    raise ValueError(f"duplicate external identifier in {kind}: {external_id}")
                seen.add(external_id)
                result = repository.upsert(
                    kind,
                    external_id,
                    record,
                    audit_actor,
                    published=(
                        publish
                        and kind in PUBLIC_ENTITY_TYPES
                        and record.get("review_status") in {"seeded", "reviewed"}
                    ),
                    preserve_published=not publish,
                )
                if kind in {"civilizations", "layers", "nodes", "edges"}:
                    repository.upsert_spatial_projection(kind, record)
                counts[result] += 1
        # Routes carry line geometry but reference places, so project them
        # only after the place and edge projections have been materialized.
        for raw in catalog.DATASETS["routes"]:
            repository.upsert_spatial_projection(
                "routes", catalog.DATASET_MODELS["routes"].model_validate(raw).model_dump(mode="json")
            )
        for kind, records in (
            ("knowledge_entities", knowledge.ENTITIES),
            ("knowledge_claims", knowledge.CLAIMS),
            ("knowledge_relationships", knowledge.RELATIONSHIPS),
        ):
            for raw in records:
                record = raw.model_dump(mode="json") if isinstance(raw, BaseModel) else dict(raw)
                if kind == "knowledge_entities":
                    record["review_status"] = record["review_state"]
                    external_id = record["slug"]
                elif kind == "knowledge_claims":
                    record["review_status"] = record["review_state"]
                    external_id = record["id"]
                else:
                    external_id = record["id"]
                result = repository.upsert(
                    kind,
                    str(external_id),
                    record,
                    audit_actor,
                    published=(
                        publish
                        and record.get("review_status") in {"seeded", "reviewed"}
                    ),
                    preserve_published=not publish,
                )
                counts[result] += 1
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actor", default="fixture:world117", help="audited importer actor name")
    parser.add_argument("--dry-run", action="store_true", help="validate and report without writing")
    parser.add_argument(
        "--publish",
        action="store_true",
        help="release public atlas entity types after validation; audit records remain private",
    )
    args = parser.parse_args()
    print(import_fixture(actor=args.actor, dry_run=args.dry_run, publish=args.publish))
