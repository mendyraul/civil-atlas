"""Validate first, archive exact bytes, then import in one database transaction."""

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from sqlalchemy import text

from app.db.session import session_scope
from app.ingestion.licenses import check_license
from app.ingestion.pleiades import SourceAdapter
from app.schemas import ImportJob, ReviewAssignment, RevisionRecord, SourceArtifact
from app.services.repository import AtlasRepository


def _json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2).encode() + b"\n"


@dataclass
class ImportBundle:
    raw: bytes
    manifest: dict[str, Any]
    adapter: SourceAdapter

    @property
    def manifest_bytes(self) -> bytes:
        return _json(self.manifest)

    @property
    def digest(self) -> str:
        return sha256(self.manifest_bytes).hexdigest()

    @property
    def job_id(self) -> str:
        version = sha256(self.manifest["dataset_version"].encode()).hexdigest()
        return f"import-{self.manifest['namespace']}-{version}"


def prepare_import(
    adapter: SourceAdapter, snapshot: Path, ids: list[str],
    dataset_version: str, retrieved_at: str,
) -> ImportBundle:
    check_license(adapter)
    if not dataset_version.strip():
        raise ValueError("dataset version must not be empty")
    try:
        timestamp = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError("timezone missing")
    except ValueError as error:
        raise ValueError("retrieved-at must be an ISO 8601 timestamp with timezone") from error
    retrieved_at = timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    raw = snapshot.read_bytes()
    normalized = adapter.normalize(raw, ids, dataset_version, retrieved_at)
    selected = normalized.selected_ids if normalized.selected_ids is not None else ids
    return ImportBundle(raw, {
        "schema_version": 1, "namespace": adapter.namespace, "adapter_version": adapter.version,
        "dataset_slug": f"{adapter.namespace}-pilot", "dataset_version": dataset_version,
        "retrieved_at": retrieved_at, "selected_ids": sorted(selected),
        "raw_sha256": sha256(raw).hexdigest(), "raw_byte_size": len(raw),
        "datasets": normalized.datasets, "omissions": normalized.omissions,
    }, adapter)


class LocalArchive:
    """Content-addressed files, published atomically without overwriting existing bytes."""

    def __init__(self, root: Path):
        self.root = root

    def put(self, bucket: str, data: bytes) -> str:
        digest = sha256(data).hexdigest()
        key = f"sha256/{digest}"
        path = self.root / bucket / key
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
            temp_path = Path(temporary.name)
            try:
                temporary.write(data)
                temporary.flush()
                os.fsync(temporary.fileno())
                try:
                    os.link(temp_path, path)
                except FileExistsError:
                    if path.read_bytes() != data:
                        raise ValueError(f"artifact integrity failure: {path}")
            finally:
                temp_path.unlink(missing_ok=True)
        return key


def import_bundle(bundle: ImportBundle, artifact_dir: Path, actor: str, *, dry_run: bool = False) -> dict:
    if not actor.strip():
        raise ValueError("actor must not be empty")
    manifest = bundle.manifest
    summary = {
        "job_id": bundle.job_id, "dataset_version": manifest["dataset_version"],
        "manifest_sha256": bundle.digest, "raw_sha256": manifest["raw_sha256"],
        "counts": {kind: len(records) for kind, records in manifest["datasets"].items()},
        "omissions": manifest["omissions"], "dry_run": dry_run,
    }
    if dry_run:
        return {**summary, "status": "validated"}
    now = datetime.now(timezone.utc).isoformat()
    audit_actor = f"{actor};dataset={manifest['dataset_slug']};version={manifest['dataset_version']};manifest_sha256={bundle.digest}"
    archive = LocalArchive(artifact_dir)
    with session_scope() as session:
        # Serialize pilot imports, including overlapping selections and concurrent retries.
        session.execute(text("SELECT pg_advisory_xact_lock(hashtext(:namespace))"),
                        {"namespace": f"ingestion:{manifest['namespace']}"})
        repository = AtlasRepository(session)
        existing = repository.get("import_jobs", bundle.job_id, published_only=False)
        if existing and existing.get("manifest_sha256") != bundle.digest:
            raise ValueError("dataset version already used with different inputs; choose a new version")
        raw_key = archive.put("raw-sources", bundle.raw)
        manifest_key = archive.put("normalized-sources", bundle.manifest_bytes)
        if existing:
            # A receipt means the entire transaction succeeded. Preserve subsequent reviews.
            return {**summary, "status": "duplicate"}

        raw_id = f"artifact-raw-{bundle.digest}"
        manifest_id = f"artifact-manifest-{bundle.digest}"

        def artifact(identifier: str, bucket: str, key: str, data: bytes, kind: str, **kwargs: Any) -> dict:
            return SourceArtifact(
                id=identifier, artifact_type=kind, storage_provider="local", bucket=bucket,
                object_key=key, mime_type="application/gzip" if data.startswith(b"\x1f\x8b") else "application/json",
                byte_size=len(data), sha256=f"sha256:{sha256(data).hexdigest()}",
                import_job_id=bundle.job_id, created_at=now, updated_at=now,
                metadata_json={"adapter_version": manifest["adapter_version"],
                               "dataset_version": manifest["dataset_version"],
                               "retrieved_at": manifest["retrieved_at"],
                               "selected_ids": manifest["selected_ids"]}, **kwargs,
            ).model_dump(mode="json")

        artifacts = [
            artifact(raw_id, "raw-sources", raw_key, bundle.raw, "raw_source_record"),
            artifact(manifest_id, "normalized-sources", manifest_key, bundle.manifest_bytes,
                     "import_manifest", derived_from_artifact_id=raw_id),
        ]
        for record in manifest["datasets"]["source_records"]:
            artifacts.append(artifact(
                f"artifact-{record['id']}-{bundle.digest}", "normalized-sources", manifest_key,
                bundle.manifest_bytes, "normalized_source_record", source_record_id=record["id"],
                derived_from_artifact_id=raw_id,
            ))
        for item in artifacts:
            repository.upsert("artifacts", item["id"], item, audit_actor)

        datasets = {kind: list(records) for kind, records in manifest["datasets"].items()}
        # If a later source loses its dates/coordinates, retire earlier renderable data.
        # Keep its last value for audit, but block approval until an eligible reimport.
        for omission in manifest["omissions"]:
            for kind, identifier in bundle.adapter.entity_ids_for(omission["id"]):
                previous = repository.get(kind, identifier, published_only=False)
                if previous:
                    datasets[kind].append({**previous, "review_status": "needs_review",
                                           "import_review_blocked": omission["reason"]})
        results = {"created": 0, "updated": 0, "duplicate": 0}
        for kind, records in datasets.items():
            for record in records:
                identifier = str(record.get("slug") or record["id"])
                payload = {**record, "import_job_id": bundle.job_id, "manifest_sha256": bundle.digest}
                result = repository.upsert(kind, identifier, payload, audit_actor, published=False)
                results[result] += 1
                if kind == "layers":
                    # The public layer query reads this PostGIS projection, gated by publication.
                    civilization_id = record["civilization_id"]
                    if not repository.get("civilizations", civilization_id, published_only=False):
                        raise ValueError(f"layer {identifier} references unknown civilization "
                                         f"{civilization_id}; import the world117 seed first")
                    repository.upsert_spatial_projection(kind, record)
                assignment = ReviewAssignment(
                    id=f"review-{kind}-{identifier}", entity_type=kind, entity_id=identifier,
                    current_review_status="needs_review", target_review_status="reviewed",
                    assigned_reviewer="atlas-editorial", assigned_by=actor, priority="medium",
                    notes=f"Review {manifest['dataset_slug']} version {manifest['dataset_version']}; manifest {bundle.digest}. "
                          + str(record.get("import_review_blocked", record.get("notes", "Verify source provenance before approval."))),
                    created_at=now,
                ).model_dump(mode="json")
                repository.upsert("review_assignments", assignment["id"], assignment, audit_actor)
                revision = RevisionRecord(
                    id=f"revision-{bundle.digest}-{kind}-{identifier}", entity_type=kind,
                    entity_id=identifier, revision_kind="external_source_import",
                    summary=f"Imported {identifier} from {manifest['dataset_slug']}",
                    diff_excerpt=f"{result}; version={manifest['dataset_version']}; manifest_sha256={bundle.digest}",
                    actor=actor, artifact_id=manifest_id, created_at=now,
                ).model_dump(mode="json")
                repository.upsert("revisions", revision["id"], revision, audit_actor)
        job = ImportJob(
            id=bundle.job_id, dataset_slug=manifest["dataset_slug"], dataset_label=bundle.adapter.label,
            status="completed", source_type=bundle.adapter.source_type, bucket="normalized-sources",
            object_prefix="sha256/", initiated_by=actor, manifest_artifact_id=manifest_id,
            started_at=now, completed_at=datetime.now(timezone.utc).isoformat(),
            records_discovered=len(manifest["selected_ids"]), records_imported=len(manifest["datasets"]["source_records"]),
            artifacts_created=len(artifacts), notes="Local snapshot import; publication requires editorial review.",
            dataset_version=manifest["dataset_version"], manifest_sha256=bundle.digest,
            adapter_version=manifest["adapter_version"],
        ).model_dump(mode="json")
        repository.upsert("import_jobs", job["id"], job, audit_actor)
    return {**summary, **results, "status": "completed"}
