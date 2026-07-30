from datetime import UTC, datetime
import os
import re

from app.core.config import settings
from app.schemas import (
    ArtifactIngestPlan,
    ArtifactIngestRequest,
    ImportJob,
    ReviewAssignment,
    RevisionRecord,
    SourceArtifact,
    SourceRecord,
    StorageBucketContract,
    StorageContractView,
)


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "record"


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _storage_contract_view() -> StorageContractView:
    storage = settings.storage
    return StorageContractView(
        provider=storage.provider,
        endpoint=storage.endpoint,
        public_base_url=storage.public_base_url,
        region=storage.region,
        use_path_style=storage.use_path_style,
        signed_url_ttl_seconds=storage.signed_url_ttl_seconds,
        raw=StorageBucketContract(
            name=storage.raw_bucket,
            prefix=storage.raw_prefix,
            purpose="Immutable raw captures, scans, notes, manifests, and dataset payloads.",
        ),
        normalized=StorageBucketContract(
            name=storage.normalized_bucket,
            prefix=storage.normalized_prefix,
            purpose="Normalized records and import manifests for atlas-native entities.",
        ),
        derived=StorageBucketContract(
            name=storage.derived_bucket,
            prefix=storage.derived_prefix,
            purpose="Derived geometry, presentation artifacts, and future vector tiles.",
        ),
        exports=StorageBucketContract(
            name=storage.exports_bucket,
            prefix=storage.exports_prefix,
            purpose="Researcher exports, classroom bundles, and shareable artifacts.",
        ),
    )


def _dataset_run_prefix(dataset_slug: str, run_date: str) -> str:
    return f"{settings.storage.normalized_prefix}/{dataset_slug}/{run_date}"


def _raw_object_key(source_namespace: str, feature_kind: str, source_record_id: str, filename: str) -> str:
    return (
        f"{settings.storage.raw_prefix}/"
        f"{_slug(source_namespace)}/{_slug(feature_kind)}/{source_record_id}/{os.path.basename(filename)}"
    )


def _normalized_object_key(dataset_slug: str, run_date: str, source_record_id: str) -> str:
    return (
        f"{_dataset_run_prefix(dataset_slug, run_date)}/"
        f"source-records/{source_record_id}.json"
    )


def _derived_object_key(layer_id: str, filename: str) -> str:
    stem, _sep, _ext = os.path.basename(filename).partition(".")
    base_name = _slug(stem or layer_id)
    return f"{settings.storage.derived_prefix}/{layer_id}/{base_name}.geojson"


def build_ingest_plan(payload: ArtifactIngestRequest) -> ArtifactIngestPlan:
    created_at = _now_iso()
    run_date = created_at[:10]
    dataset_slug = _slug(payload.dataset_slug)
    import_job_id = f"import-job-{dataset_slug}-{run_date}"
    manifest_artifact_id = f"artifact-import-manifest-{dataset_slug}-{run_date}"

    source_records: list[SourceRecord] = []
    artifacts: list[SourceArtifact] = []
    review_assignments: list[ReviewAssignment] = []
    revision_records: list[RevisionRecord] = []

    manifest_artifact = SourceArtifact(
        id=manifest_artifact_id,
        artifact_type="import_manifest",
        storage_provider=settings.storage.provider,
        bucket=settings.storage.normalized_bucket,
        object_key=f"{_dataset_run_prefix(dataset_slug, run_date)}/manifest.json",
        mime_type="application/json",
        byte_size=max(2048, 512 * max(len(payload.records), 1)),
        sha256=f"sha256:manifest-{dataset_slug}-{run_date}",
        import_job_id=import_job_id,
        metadata_json={
            "dataset_slug": dataset_slug,
            "record_count": len(payload.records),
            "planned_outputs": ["raw_source_record", "normalized_source_record", "derived_geometry"],
        },
        created_at=created_at,
        updated_at=created_at,
    )

    for index, record in enumerate(payload.records, start=1):
        source_record = SourceRecord(
            id=record.source_record_id,
            feature_id=record.feature_id,
            feature_kind=record.feature_kind,
            feature_label=record.feature_label,
            title=record.title,
            citation=record.citation,
            link=record.link,
            source_namespace=record.source_namespace,
            confidence=record.confidence,
            review_status=record.review_status,
            notes=record.notes,
            valid_from_year=record.valid_from_year,
            valid_to_year=record.valid_to_year,
        )
        source_records.append(source_record)

        raw_artifact = SourceArtifact(
            id=f"artifact-raw-{record.source_record_id}",
            artifact_type="raw_source_record",
            storage_provider=settings.storage.provider,
            bucket=settings.storage.raw_bucket,
            object_key=_raw_object_key(
                record.source_namespace,
                record.feature_kind,
                record.source_record_id,
                record.filename,
            ),
            mime_type=record.mime_type,
            byte_size=record.byte_size,
            sha256=record.sha256,
            source_record_id=record.source_record_id,
            claim_id=record.claim_id,
            layer_id=record.layer_id,
            import_job_id=import_job_id,
            derived_from_artifact_id=manifest_artifact_id,
            metadata_json={
                "feature_id": record.feature_id,
                "feature_kind": record.feature_kind,
                "feature_label": record.feature_label,
                "filename": record.filename,
                **record.metadata_json,
            },
            created_at=created_at,
            updated_at=created_at,
        )
        artifacts.append(raw_artifact)

        normalized_artifact = SourceArtifact(
            id=f"artifact-normalized-{record.source_record_id}",
            artifact_type="normalized_source_record",
            storage_provider=settings.storage.provider,
            bucket=settings.storage.normalized_bucket,
            object_key=_normalized_object_key(dataset_slug, run_date, record.source_record_id),
            mime_type="application/json",
            byte_size=max(1024, record.byte_size // 2),
            sha256=f"sha256:normalized-{record.source_record_id}",
            source_record_id=record.source_record_id,
            claim_id=record.claim_id,
            layer_id=record.layer_id,
            import_job_id=import_job_id,
            derived_from_artifact_id=raw_artifact.id,
            metadata_json={
                "dataset_slug": dataset_slug,
                "normalization_index": index,
                "source_namespace": record.source_namespace,
            },
            created_at=created_at,
            updated_at=created_at,
        )
        artifacts.append(normalized_artifact)

        revision_records.append(
            RevisionRecord(
                id=f"revision-ingest-{record.source_record_id}",
                entity_type="source_record",
                entity_id=record.source_record_id,
                revision_kind="source_artifact_ingest",
                summary=f"Ingested source record {record.source_record_id} into the {dataset_slug} pipeline.",
                diff_excerpt=(
                    f"Linked raw object {raw_artifact.object_key} to normalized record "
                    f"{normalized_artifact.object_key} under import job {import_job_id}."
                ),
                actor=payload.initiated_by,
                artifact_id=normalized_artifact.id,
                review_decision_id=None,
                created_at=created_at,
            )
        )

        if record.review_status != "reviewed":
            review_assignments.append(
                ReviewAssignment(
                    id=f"review-assignment-source-record-{record.source_record_id}",
                    entity_type="source_record",
                    entity_id=record.source_record_id,
                    current_review_status=record.review_status,
                    target_review_status="reviewed",
                    assigned_reviewer="atlas-editorial",
                    assigned_by=payload.initiated_by,
                    priority="high" if record.create_derived_geometry else "medium",
                    due_at=None,
                    notes=(
                        f"Confirm source record {record.source_record_id} and its normalized lineage "
                        f"before the atlas treats it as settled evidence."
                    ),
                    created_at=created_at,
                )
            )

        if record.create_derived_geometry and record.layer_id:
            derived_artifact = SourceArtifact(
                id=f"artifact-derived-{record.layer_id}-{record.source_record_id}",
                artifact_type="derived_geometry",
                storage_provider=settings.storage.provider,
                bucket=settings.storage.derived_bucket,
                object_key=_derived_object_key(record.layer_id, record.filename),
                mime_type="application/geo+json",
                byte_size=max(2048, record.byte_size),
                sha256=f"sha256:derived-{record.layer_id}-{record.source_record_id}",
                source_record_id=record.source_record_id,
                claim_id=record.claim_id,
                layer_id=record.layer_id,
                import_job_id=import_job_id,
                derived_from_artifact_id=normalized_artifact.id,
                metadata_json={
                    "dataset_slug": dataset_slug,
                    "feature_id": record.feature_id,
                    "feature_kind": record.feature_kind,
                },
                created_at=created_at,
                updated_at=created_at,
            )
            artifacts.append(derived_artifact)

            revision_records.append(
                RevisionRecord(
                    id=f"revision-derived-{record.layer_id}-{record.source_record_id}",
                    entity_type="civilization_layer",
                    entity_id=record.layer_id,
                    revision_kind="derived_geometry_plan",
                    summary=f"Planned derived geometry artifact for {record.layer_id}.",
                    diff_excerpt=(
                        f"Derived geometry will land at {derived_artifact.object_key} "
                        f"from normalized source record {normalized_artifact.object_key}."
                    ),
                    actor=payload.initiated_by,
                    artifact_id=derived_artifact.id,
                    review_decision_id=None,
                    created_at=created_at,
                )
            )

            review_assignments.append(
                ReviewAssignment(
                    id=f"review-assignment-layer-{record.layer_id}-{record.source_record_id}",
                    entity_type="civilization_layer",
                    entity_id=record.layer_id,
                    current_review_status="needs_review",
                    target_review_status="reviewed",
                    assigned_reviewer="atlas-geometry-review",
                    assigned_by=payload.initiated_by,
                    priority="high",
                    due_at=None,
                    notes=(
                        f"Review planned derived geometry for {record.layer_id} sourced from "
                        f"{record.source_record_id} before promotion."
                    ),
                    created_at=created_at,
                )
            )

    import_job = ImportJob(
        id=import_job_id,
        dataset_slug=dataset_slug,
        dataset_label=payload.dataset_label,
        status="planned",
        source_type=payload.source_type,
        bucket=settings.storage.normalized_bucket,
        object_prefix=f"{_dataset_run_prefix(dataset_slug, run_date)}/",
        initiated_by=payload.initiated_by,
        manifest_artifact_id=manifest_artifact.id,
        started_at=created_at,
        completed_at=None,
        records_discovered=len(payload.records),
        records_imported=len(payload.records),
        artifacts_created=1 + len(artifacts),
        notes=payload.notes or "Planned import bundle generated from the active storage contract.",
    )

    return ArtifactIngestPlan(
        storage=_storage_contract_view(),
        import_job=import_job,
        manifest_artifact=manifest_artifact,
        source_records=source_records,
        artifacts=[manifest_artifact, *artifacts],
        review_assignments=review_assignments,
        revision_records=revision_records,
    )
