"""Load the versioned knowledge manifest for import and learning references."""

import json
from hashlib import sha256
from pathlib import Path

from app.schemas import ClaimView, KnowledgeEntity

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "data/imports/knowledge/v1/manifest.json"
MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
MANIFEST_SHA256 = sha256(MANIFEST_PATH.read_bytes()).hexdigest()
DATASET_VERSION = str(MANIFEST["dataset_version"])
DATASETS = MANIFEST["datasets"]
ENTITIES = [KnowledgeEntity.model_validate(item) for item in DATASETS["entities"]]
CLAIMS = [ClaimView.model_validate(item) for item in DATASETS["claims"]]
RELATIONSHIPS = DATASETS["relationships"]

ENTITIES_BY_SLUG = {entity.slug: entity for entity in ENTITIES}
CLAIMS_BY_ID = {claim.id: claim for claim in CLAIMS}
