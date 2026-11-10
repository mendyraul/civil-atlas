"""Export/load reviewed public data: python -m app.data_release --help."""

import argparse
from collections import Counter
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
from urllib.request import build_opener, HTTPRedirectHandler
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
VERSION_PATTERN = r"\d{4}\.(?:0[1-9]|1[0-2])(?:\.[0-9]+)?"


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


class ReleaseRepository:
    """Read-only public-record index used by the normal curated validators."""

    def __init__(self, records):
        self.records = records
        self.index = {}
        for item in records:
            for identifier in {item["external_id"], str(item["payload"]["id"])}:
                key = item["entity_type"], identifier
                previous = self.index.get(key)
                if previous is not None and previous["id"] != item["payload"]["id"]:
                    raise ValueError(f"ambiguous public identifier {key}")
                self.index[key] = item["payload"]

    def get(self, kind, identifier, **kwargs):
        return self.index.get((kind, identifier))

    def list(self, kind, **kwargs):
        return [item["payload"] for item in self.records if item["entity_type"] == kind]


def notice_bytes(name):
    for folder in (ROOT, Path(__file__).resolve().parents[1] / "release-notices"):
        path = folder / name
        if path.is_file():
            return path.read_bytes()
    raise ValueError(f"release notice {name} is missing from the checkout/image")


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
        if payload.get("import_review_blocked"):
            raise ValueError(f"{kind}/{identifier}: source review remains blocked")
        state = payload.get("review_status", payload.get("review_state"))
        if state is not None and state not in {"reviewed", "seeded"}:
            raise ValueError(f"{kind}/{identifier}: record is not reviewed for release")
        model = MODELS[kind]
        # Restrict release payloads to the public schema, excluding ingestion/storage metadata.
        value = model.model_validate(
            {k: v for k, v in payload.items() if k in model.model_fields}
        ).model_dump(mode="json")
        for field in (
            "source_record_ids",
            "claim_ids",
            "source_id",
            "source_ids",
            "statement",
            "qualifiers",
            "date_citation",
            "source_properties",
            "review_status",
        ):
            if field in payload:
                value[field] = payload[field]
        for field in ("source_record_ids", "claim_ids", "source_ids"):
            if field in value and (
                not isinstance(value[field], list)
                or any(
                    not isinstance(identifier, str) or not identifier
                    for identifier in value[field]
                )
            ):
                raise ValueError(
                    f"{kind}/{identifier}: {field} must contain string identifiers"
                )
        if value.get("is_placeholder") or value.get("geometry_placeholder"):
            raise ValueError(
                f"{kind}/{identifier}: placeholder geometry is not release data"
            )
        for first, last in [
            ("start_year", "end_year"),
            ("valid_from_year", "valid_to_year"),
        ]:
            if (
                value.get(first) is not None
                and value.get(last) is not None
                and value[first] > value[last]
            ):
                raise ValueError(f"{kind}/{identifier}: dates are reversed")
        if identifier != str(value.get("slug") or value["id"]):
            raise ValueError("external identifier differs from canonical identifier")
        keys.add((kind, identifier))
        if (kind, str(value["id"])) in aliases:
            raise ValueError("duplicate canonical entity ID")
        aliases[kind, str(value["id"])] = identifier
        clean.append(dict(entity_type=kind, external_id=identifier, payload=value))
    index = ReleaseRepository(clean)
    refs = {
        "source_record_ids": "source_records",
        "claim_ids": "claims",
        "source_id": "sources",
        "source_ids": "sources",
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
        "overview_claim_ids": "knowledge_claims",
        "chronology_event_ids": "knowledge_entities",
        "related_entity_ids": "knowledge_entities",
        "passage_ids": "knowledge_entities",
    }
    kind_alias = {
        "civilization": ("civilizations",),
        "civilization_layer": ("layers",),
        "node": ("nodes",),
        "place": ("places",),
        "route": ("routes",),
        "historical_event": ("events",),
        "person": ("people", "knowledge_entities"),
        "office": ("offices", "knowledge_entities"),
        "concept": ("knowledge_entities",),
    }

    def require(kinds, identifier, owner):
        if isinstance(kinds, str):
            kinds = (kinds,)
        if not isinstance(identifier, str) or not any(
            index.get(kind, identifier) for kind in kinds
        ):
            raise ValueError(
                f"{owner}: missing public dependency {'|'.join(kinds)}/{identifier}"
            )

    def direct_refs(value, owner):
        # Source properties, qualifier bindings and geographic literals are opaque
        # provenance, not a second schema of canonical application references.
        for field, kind in refs.items():
            content = value.get(field)
            if content is None:
                continue
            identifiers = content if isinstance(content, list) else [content]
            for identifier in identifiers:
                require(kind, identifier, owner)

    for item in clean:
        kind, payload = item["entity_type"], item["payload"]
        owner = f"{kind}/{item['external_id']}"
        direct_refs(payload, owner)
        if kind in {"claims", "relationships"}:
            for field in ("subject", "object", "target"):
                identifier = payload.get(field + "_id")
                if identifier:
                    require(
                        kind_alias.get(
                            payload.get(field + "_kind"), tuple(PUBLIC_ENTITY_TYPES)
                        ),
                        identifier,
                        owner,
                    )
        if kind == "evidence":
            require(
                kind_alias.get(
                    payload.get("entity_type"), (payload.get("entity_type"),)
                ),
                payload["entity_id"],
                owner,
            )
        if kind in {"knowledge_claims", "knowledge_relationships"}:
            for field in ("subject_id", "object_id", "target_id"):
                if payload.get(field):
                    require("knowledge_entities", payload[field], owner)
        if kind == "knowledge_entities":
            for layer in payload.get("map_layers", []):
                if layer.get("id"):
                    require("layers", layer["id"], owner)
        if kind == "annotations":
            from app.services.episodes import validate_annotation

            validate_annotation(Annotation.model_validate(payload), index)
        if kind == "episodes":
            from app.services.episodes import validate_episode

            pack = EpisodePack.model_validate(payload)
            for step in payload["steps"]:
                direct_refs(step, owner)
            for annotation in payload["annotations"]:
                direct_refs(annotation, owner)
            validate_episode(pack, index)

    return clean


def source_versions(records):
    return [
        {
            key: item["payload"].get(key)
            for key in ("id", "dataset_version", "license", "url")
        }
        for item in records
        if item["entity_type"] == "sources"
    ]


def build_archive(records, version):
    if not re.fullmatch(VERSION_PATTERN, version):
        raise ValueError("version must be YYYY.MM or YYYY.MM.PATCH")
    records = validate_records(records)
    files = {
        "records.json": encode(records),
        "ATTRIBUTION.md": notice_bytes("ATTRIBUTION.md"),
        "DATA_LICENSE.md": notice_bytes("DATA_LICENSE.md"),
    }
    manifest = {
        "schema_version": 1,
        "version": version,
        "counts": dict(Counter(x["entity_type"] for x in records)),
        "source_versions": source_versions(records),
        "files": {name: sha256(value).hexdigest() for name, value in files.items()},
    }
    files["manifest.json"] = encode(manifest)
    if sum(len(value) for value in files.values()) > MAX_BYTES:
        raise ValueError("expanded release exceeds size limit")
    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, value in sorted(files.items()):
            archive.writestr(name, value)
    raw = output.getvalue()
    if len(raw) > MAX_BYTES:
        raise ValueError("release exceeds size limit")
    return raw, manifest


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
    if not re.fullmatch(VERSION_PATTERN, str(manifest.get("version", ""))):
        raise ValueError("invalid release version")
    records = validate_records(json.loads(files["records.json"]))
    if dict(Counter(x["entity_type"] for x in records)) != manifest.get("counts"):
        raise ValueError("record counts differ from manifest")
    if source_versions(records) != manifest.get("source_versions"):
        raise ValueError("source versions differ from release records")
    return records, manifest


def preserve_release_links(records, provenance):
    sources = [
        item["payload"] for item in provenance if item["entity_type"] == "sources"
    ]
    evidence = [
        item["payload"] for item in provenance if item["entity_type"] == "evidence"
    ]
    for item in records:
        payload = item["payload"]
        if (
            item["entity_type"] != "source_records"
            or payload.get("source_id")
            or payload.get("source_ids")
        ):
            continue
        if not payload.get("import_job_id"):
            continue
        identifiers = {
            link["source_id"]
            for link in evidence
            if link.get("entity_id") == payload.get("feature_id")
            and link.get("source_id")
        }
        if not identifiers:
            identifiers = {
                source["id"]
                for source in sources
                if source.get("import_job_id") == payload["import_job_id"]
            }
        if not identifiers:
            raise ValueError(
                f"source_records/{payload['id']}: imported citation has no source-release identity"
            )
        payload["source_ids"] = sorted(identifiers)


def export_release(version, output, dry_run=False):
    with session_scope() as session:
        session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
        rows = session.execute(
            text(
                "SELECT entity_type,external_id,payload FROM atlas_entities WHERE published=TRUE ORDER BY entity_type,external_id"
            )
        ).mappings()
        records = [dict(row) for row in rows]
        provenance = session.execute(
            text(
                "SELECT entity_type,payload FROM atlas_entities WHERE entity_type IN ('sources','evidence')"
            )
        ).mappings()
        preserve_release_links(records, [dict(row) for row in provenance])
        raw, manifest = build_archive(records, version)
    if not dry_run:
        with Path(output).open("xb") as stream:
            stream.write(raw)
    return manifest


class HTTPSOnlyRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        if urlparse(newurl).scheme != "https":
            raise ValueError("release redirects require HTTPS")
        return super().redirect_request(request, fp, code, message, headers, newurl)


def release_bytes(source):
    if str(source).startswith(("http://", "https://")):
        if urlparse(str(source)).scheme != "https":
            raise ValueError("release URLs require HTTPS")
        with build_opener(HTTPSOnlyRedirect()).open(
            str(source), timeout=30
        ) as response:
            raw = response.read(MAX_BYTES + 1)
    else:
        with Path(source).open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("release exceeds size limit")
    return raw


def validate_release(source, expected_version=None, expected_sha256=None, output=None):
    raw = release_bytes(source)
    if expected_sha256 is not None and (
        not re.fullmatch(r"[a-f0-9]{64}", expected_sha256)
        or sha256(raw).hexdigest() != expected_sha256
    ):
        raise ValueError("release file SHA-256 differs from the expected digest")
    _, manifest = read_archive(raw)
    if expected_version is not None and manifest["version"] != expected_version:
        raise ValueError("release version differs from the expected version")
    if output:
        with Path(output).open("xb") as stream:
            stream.write(raw)
    return manifest


def load_release(source, dry_run=False):
    raw = release_bytes(source)
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
    validate = sub.add_parser("validate")
    validate.add_argument("source")
    validate.add_argument("--version")
    validate.add_argument("--sha256")
    validate.add_argument("--output")
    args = parser.parse_args()
    try:
        if args.command == "export":
            result = export_release(args.version, args.output, args.dry_run)
        elif args.command == "load":
            result = load_release(args.source, args.dry_run)
        else:
            result = validate_release(
                args.source, args.version, args.sha256, args.output
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
