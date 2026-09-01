"""Versioned region and era-pack registry for controlled coverage growth."""

from __future__ import annotations

import json
from pathlib import Path

from app.schemas import CoveragePack


MANIFEST_PATH = Path(__file__).resolve().parents[2] / "data/imports/coverage/v1/manifest.json"
MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
if MANIFEST.get("schema_version") != 1:
    raise RuntimeError("unsupported coverage manifest schema version")

COVERAGE_PACKS = [CoveragePack.model_validate(item) for item in MANIFEST.get("packs", [])]
if len({pack.id for pack in COVERAGE_PACKS}) != len(COVERAGE_PACKS):
    raise RuntimeError("coverage pack identifiers must be unique")


__all__ = ["COVERAGE_PACKS", "CoveragePack", "MANIFEST_PATH"]
