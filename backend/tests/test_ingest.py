import pytest
from pydantic import ValidationError
from app.schemas import ArtifactIngestRequest
from app.services.ingest import build_ingest_plan

def record(**overrides):
    base=dict(source_record_id='source-x',feature_id='rome',feature_kind='civilization',feature_label='Rome',title='Evidence',citation='Citation',source_namespace='test',confidence='high',review_status='seeded',notes='',valid_from_year=-44,valid_to_year=117,filename='../capture.json',mime_type='application/json',byte_size=42,sha256='sha256:abc',metadata_json={},create_derived_geometry=False)
    base.update(overrides); return base

def test_ingest_rejects_invalid_intervals():
    with pytest.raises(ValidationError): ArtifactIngestRequest(dataset_slug='fixture',dataset_label='Fixture',source_type='dataset',initiated_by='test',records=[record(valid_from_year=10,valid_to_year=-10)])

def test_ingest_preserves_provenance_and_sanitizes_paths():
    payload=ArtifactIngestRequest(dataset_slug='Fixture Set',dataset_label='Fixture',source_type='dataset',initiated_by='test',records=[record()])
    plan=build_ingest_plan(payload); raw=next(a for a in plan.artifacts if a.artifact_type=='raw_source_record')
    assert raw.source_record_id=='source-x' and raw.derived_from_artifact_id==plan.import_job.manifest_artifact_id
    assert '..' not in raw.object_key
