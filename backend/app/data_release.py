"""Export/load reviewed public data: python -m app.data_release --help."""

import argparse
from collections import Counter
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
from urllib.request import urlopen
from urllib.parse import urlparse
import zipfile

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.db.session import session_scope
from app.services.atlas import MODEL_TYPES
from app.services.repository import AtlasRepository, PUBLIC_ENTITY_TYPES
from app.schemas.toolkit import Annotation, EpisodePack

ROOT = Path(__file__).resolve().parents[2]
MAX_BYTES = 250 * 1024 * 1024
FILES = {"records.json", "manifest.json", "ATTRIBUTION.md", "DATA_LICENSE.md"}


class KnowledgeRelationship(BaseModel):
    id: str
    relationship_type: str
    subject_id: str
    target_id: str
    valid_from_year: int
    valid_to_year: int
    review_status: str
    supporting_claim_ids: list[str]


MODELS = {
    **MODEL_TYPES,
    "episodes": EpisodePack,
    "annotations": Annotation,
    "knowledge_relationships": KnowledgeRelationship,
}


def encode(value):
    return (
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode()
        + b"\n"
    )


def validate_records(records):
    if not isinstance(records, list):
        raise ValueError("records must be an array")
    keys = set()
    aliases = {}
    clean = []
    for item in records:
        if not isinstance(item, dict) or not isinstance(item.get("payload"), dict):
            raise ValueError("each record requires a payload object")
        kind = item.get("entity_type")
        identifier = item.get("external_id")
        payload = item.get("payload")
        if kind not in PUBLIC_ENTITY_TYPES or kind not in MODELS:
            raise ValueError(f"unsupported public entity type {kind}")
        if (
            not isinstance(identifier, str)
            or not identifier
            or (kind, identifier) in keys
        ):
            raise ValueError("missing or duplicate external identifier")
        model = MODELS[kind]
        # Restrict release payloads to the public schema, excluding ingestion/storage metadata.
        value = model.model_validate(
            {k: v for k, v in payload.items() if k in model.model_fields}
        ).model_dump(mode="json")
        for field in (
            "source_record_ids",
            "claim_ids",
            "source_id",
            "statement",
            "qualifiers",
            "date_citation",
            "source_properties",
            "review_status",
        ):
            if field in payload:
                value[field] = payload[field]
        if identifier != str(value.get("slug") or value["id"]):
            raise ValueError("external identifier differs from canonical identifier")
        keys.add((kind, identifier))
        if (kind, str(value["id"])) in aliases:
            raise ValueError("duplicate canonical entity ID")
        aliases[kind, str(value["id"])] = identifier
        clean.append(dict(entity_type=kind, external_id=identifier, payload=value))
    refs = {
        "source_record_ids": "source_records",
        "claim_ids": "claims",
        "source_id": "sources",
        "civilization_id": "civilizations",
        "civilization_ids": "civilizations",
        "source_node_id": "nodes",
        "target_node_id": "nodes",
        "source_place_id": "places",
        "target_place_id": "places",
        "place_id": "places",
        "place_ids": "places",
        "person_id": "people",
        "layer_ids": "layers",
        "boundary_layer_id": "layers",
        "annotation_ids": "annotations",
        "supporting_claim_ids": "knowledge_claims",
    }

    def require(kind, identifier, owner):
        if (kind, str(identifier)) not in keys and (
            kind,
            str(identifier),
        ) not in aliases:
            raise ValueError(f"{owner}: missing public dependency {kind}/{identifier}")

    def walk(value, owner):
        if isinstance(value, list):
            for item in value:
                walk(item, owner)
        if not isinstance(value, dict):
            return
        for field, content in value.items():
            if field in refs and content is not None:
                for identifier in content if isinstance(content, list) else [content]:
                    require(refs[field], identifier, owner)
            elif isinstance(content, (dict, list)):
                walk(content, owner)

    kind_alias = {
        "civilization": "civilizations",
        "civilization_layer": "layers",
        "node": "nodes",
        "place": "places",
        "route": "routes",
        "historical_event": "events",
    }
    for item in clean:
        payload = item["payload"]
        owner = f"{item['entity_type']}/{item['external_id']}"
        walk(payload, owner)
        for field in ("subject", "object"):
            target_kind = kind_alias.get(payload.get(field + "_kind"))
            if target_kind and payload.get(field + "_id"):
                require(target_kind, payload[field + "_id"], owner)
        if item["entity_type"] == "knowledge_relationships":
            for field in ("subject_id", "target_id"):
                require("knowledge_entities", payload[field], owner)
    return clean


def build_archive(records, version):
    if not re.fullmatch(r"\d{4}\.\d{2}(?:\.[0-9]+)?", version):
        raise ValueError("version must be YYYY.MM or YYYY.MM.PATCH")
    records = validate_records(records)
    files = {
        "records.json": encode(records),
        "ATTRIBUTION.md": (ROOT / "ATTRIBUTION.md").read_bytes(),
        "DATA_LICENSE.md": (ROOT / "DATA_LICENSE.md").read_bytes(),
    }
    manifest = {
        "schema_version": 1,
        "version": version,
        "counts": dict(Counter(x["entity_type"] for x in records)),
        "source_versions": [
            {
                k: x["payload"].get(k)
                for k in ("id", "dataset_version", "license", "url")
            }
            for x in records
            if x["entity_type"] == "sources"
        ],
        "files": {name: sha256(value).hexdigest() for name, value in files.items()},
    }
    files["manifest.json"] = encode(manifest)
    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, value in sorted(files.items()):
            archive.writestr(name, value)
    return output.getvalue(), manifest


def read_archive(raw):
    if len(raw) > MAX_BYTES:
        raise ValueError("release exceeds size limit")
    try:
        with zipfile.ZipFile(BytesIO(raw)) as archive:
            names = archive.namelist()
            if set(names) != FILES or len(names) != len(FILES):
                raise ValueError("unexpected or duplicate archive members")
            if sum(info.file_size for info in archive.infolist()) > MAX_BYTES:
                raise ValueError("expanded release exceeds size limit")
            files = {name: archive.read(name) for name in names}
    except (zipfile.BadZipFile, RuntimeError) as error:
        raise ValueError("invalid release archive") from error
    manifest = json.loads(files["manifest.json"])
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported release schema version")
    if set(manifest.get("files", {})) != FILES - {"manifest.json"}:
        raise ValueError("incomplete checksum manifest")
    for name, digest in manifest["files"].items():
        if sha256(files[name]).hexdigest() != digest:
            raise ValueError(f"checksum mismatch: {name}")
    if not re.fullmatch(r"\d{4}\.\d{2}(?:\.[0-9]+)?", str(manifest.get("version", ""))):
        raise ValueError("invalid release version")
    records = validate_records(json.loads(files["records.json"]))
    if dict(Counter(x["entity_type"] for x in records)) != manifest.get("counts"):
        raise ValueError("record counts differ from manifest")
    return records, manifest


def export_release(version, output, dry_run=False):
    with session_scope() as session:
        session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
        rows = session.execute(
            text(
                "SELECT entity_type,external_id,payload FROM atlas_entities WHERE published=TRUE ORDER BY entity_type,external_id"
            )
        ).mappings()
        raw, manifest = build_archive([dict(row) for row in rows], version)
    if not dry_run:
        with Path(output).open("xb") as stream:
            stream.write(raw)
    return manifest


def load_release(source, dry_run=False):
    if str(source).startswith(("http://", "https://")):
        if urlparse(str(source)).scheme != "https":
            raise ValueError("release URLs require HTTPS")
        with urlopen(str(source), timeout=30) as response:
            if urlparse(response.url).scheme != "https":
                raise ValueError("redirect must remain HTTPS")
            raw = response.read(MAX_BYTES + 1)
    else:
        raw = Path(source).read_bytes()
    records, manifest = read_archive(raw)
    with session_scope() as session:
        session.execute(text("LOCK TABLE atlas_entities IN EXCLUSIVE MODE"))
        if session.execute(
            text("SELECT EXISTS(SELECT 1 FROM atlas_entities)")
        ).scalar_one():
            raise ValueError("release load requires an empty migrated database")
        if dry_run:
            return manifest
        repo = AtlasRepository(session)
        for item in records:
            repo.upsert(
                item["entity_type"],
                item["external_id"],
                item["payload"],
                f"release:{manifest['version']}",
                published=True,
            )
        order = {
            "people": -2,
            "offices": -1,
            "civilizations": 0,
            "places": 1,
            "nodes": 2,
            "layers": 3,
            "edges": 4,
            "routes": 5,
        }
        for item in sorted(
            records, key=lambda item: order.get(item["entity_type"], 99)
        ):
            repo.upsert_knowledge_projection(item["entity_type"], item["payload"])
            if item["entity_type"] in order:
                repo.upsert_spatial_projection(item["entity_type"], item["payload"])
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    export = sub.add_parser("export")
    export.add_argument("--version", required=True)
    export.add_argument("--output", required=True)
    export.add_argument("--dry-run", action="store_true")
    load = sub.add_parser("load")
    load.add_argument("source")
    load.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = (
            export_release(args.version, args.output, args.dry_run)
            if args.command == "export"
            else load_release(args.source, args.dry_run)
        )
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, f"Release failed: {error}\n")
    except SQLAlchemyError:
        parser.exit(
            1,
            "Release failed: database validation or transaction could not complete. Verify migrations and retry.\n",
        )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
