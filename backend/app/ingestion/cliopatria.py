"""Pure Cliopatria (Seshat) GeoJSON normalization; no network, filesystem, or database writes.

Cliopatria publishes polity borders as rows with FromYear/ToYear ranges and Wikidata IDs.
Each selected row becomes an alternative boundary layer (a "boundary_variant") on an existing
Civil Atlas civilization, linked through a Wikidata crosswalk. Everything lands as
needs_review; editors decide whether it replaces or sits beside the seeded geometry.
"""

from io import BytesIO
import json
from pathlib import Path
import re
from typing import Any
import zipfile

from app.ingestion.pleiades import NormalizedSnapshot
from app.schemas import CivilizationLayer, EvidenceLink, HistoricalClaim, Source, SourceRecord

LICENSE = "https://creativecommons.org/licenses/by/4.0/"
REPOSITORY = "https://github.com/Seshat-Global-History-Databank/cliopatria"
PAPER = (
    "Bennett, J. S. et al. Cliopatria - A geospatial database of world-wide political entities "
    "from 3400BCE to 2024CE. Scientific Data 12, 247 (2025). https://doi.org/10.1038/s41597-025-04516-9"
)
RATIONALE = (
    "Low confidence pending editorial review. Cliopatria records one scholarly reading of each "
    "polity's territory over a year range; borders are approximate and contested."
)
DEFAULT_CROSSWALK = Path(__file__).resolve().parents[2] / "data/imports/crosswalks/cliopatria-world117.json"


def _year_slug(year: int) -> str:
    return f"{-year}bce" if year < 0 else f"{year}ce"


def _load_collection(raw: bytes) -> dict[str, Any]:
    if raw.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(BytesIO(raw)) as archive:
                members = [n for n in archive.namelist() if n.endswith(".geojson") and "/" not in n]
                if len(members) != 1:
                    raise ValueError("Cliopatria zip must contain exactly one top-level .geojson file")
                raw = archive.read(members[0])
        except zipfile.BadZipFile as error:
            raise ValueError("snapshot is not a valid zip archive") from error
    try:
        data = json.loads(raw)
    except ValueError as error:
        raise ValueError("snapshot must be Cliopatria GeoJSON or its release zip") from error
    if not isinstance(data, dict) or data.get("type") != "FeatureCollection" or not isinstance(data.get("features"), list):
        raise ValueError("expected a Cliopatria GeoJSON FeatureCollection")
    if not isinstance(data.get("name"), str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", data["name"]):
        raise ValueError("Cliopatria collection name (its release label) is required")
    return data


def load_crosswalk(path: Path = DEFAULT_CROSSWALK) -> dict[str, dict[str, str]]:
    data = json.loads(path.read_text())
    crosswalk = {}
    for entry in data["polities"]:
        qid = entry["wikidata"]
        if not re.fullmatch(r"Q[0-9]+", qid) or qid in crosswalk:
            raise ValueError(f"crosswalk has an invalid or duplicate Wikidata ID: {qid}")
        crosswalk[qid] = {"civilization_id": entry["civilization_id"], "variant_group": entry["variant_group"]}
        if "cliopatria_name" in entry:
            name = entry["cliopatria_name"]
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"{qid}: cliopatria_name must be a nonempty source name")
            crosswalk[qid]["cliopatria_name"] = name
    return crosswalk


class CliopatriaAdapter:
    namespace = "cliopatria"
    version = "2"
    label = "Cliopatria (Seshat) borders"
    license = LICENSE
    source_type = "historical_gis"

    def __init__(self, year: int, crosswalk: dict[str, dict[str, str]] | None = None):
        self.year = year
        self.crosswalk = crosswalk if crosswalk is not None else load_crosswalk()

    def entity_ids_for(self, external_id: str) -> list[tuple[str, str]]:
        # Layer IDs include each row's year range, so a missing row cannot be traced back to
        # an earlier layer here. Earlier imports stay as they are for editors to retire.
        return []

    def normalize(
        self, raw: bytes, ids: list[str], dataset_version: str, retrieved_at: str
    ) -> NormalizedSnapshot:
        if len(set(ids)) != len(ids):
            raise ValueError("selected Wikidata IDs must not repeat")
        if any(not re.fullmatch(r"Q[0-9]+", qid) for qid in ids):
            raise ValueError("Cliopatria selections are Wikidata IDs such as Q12544")
        unknown = set(ids) - self.crosswalk.keys()
        if unknown:
            raise ValueError(f"no Civil Atlas civilization mapped for: {', '.join(sorted(unknown))}")
        wanted = set(ids or self.crosswalk)
        data = _load_collection(raw)
        release = data["name"]

        rows: dict[str, dict[str, Any]] = {}
        unmapped: list[dict[str, str]] = []
        for feature in data["features"]:
            props = feature.get("properties") if isinstance(feature, dict) else None
            if not isinstance(props, dict) or props.get("Type", "POLITY") != "POLITY":
                continue
            start, end = props.get("FromYear"), props.get("ToYear")
            if type(start) is not int or type(end) is not int or not start <= self.year <= end:
                continue
            qid = props.get("Wikidata")
            if qid in wanted:
                expected_name = self.crosswalk[qid].get("cliopatria_name")
                if expected_name and props.get("Name") != expected_name:
                    raise ValueError(
                        f"{qid}: source identity mismatch; expected {expected_name!r}, "
                        f"found {props.get('Name')!r}"
                    )
                if qid in rows:
                    raise ValueError(f"{qid}: more than one Cliopatria row is active in {self.year}")
                rows[qid] = feature
            elif not ids and isinstance(props.get("Name"), str):
                unmapped.append({"id": str(qid or props["Name"]),
                                 "reason": f"{props['Name']}: no Civil Atlas civilization mapped"})

        omissions = [{"id": qid, "reason": f"no Cliopatria row active in {self.year}"}
                     for qid in sorted(wanted - rows.keys())]
        omissions += sorted(unmapped, key=lambda o: o["id"])

        source_id = f"cliopatria-source-{release}"
        citation = f"{PAPER}. Data release {release}, Seshat Global History Databank, {REPOSITORY}. CC BY 4.0."
        source = Source(
            id=source_id, source_name=f"Cliopatria ({release})", source_type=self.source_type,
            external_id=release, url=REPOSITORY, citation=citation, license=LICENSE,
            dataset_version=dataset_version, reliability_tier="unreviewed",
            retrieved_at=retrieved_at, created_at=retrieved_at, updated_at=retrieved_at,
        ).model_dump(mode="json")
        source["review_status"] = "needs_review"
        datasets: dict[str, list[dict[str, Any]]] = {
            "sources": [source], "source_records": [], "claims": [], "layers": [], "evidence": [],
        }

        for qid, feature in sorted(rows.items()):
            props = feature["properties"]
            name = props.get("Name")
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"{qid}: Name is required")
            start, end = props["FromYear"], props["ToYear"]
            target = self.crosswalk[qid]
            civilization_id = target["civilization_id"]
            key = f"{civilization_id}-{_year_slug(start)}-{_year_slug(end)}"
            layer_id, record_id = f"cliopatria-{key}", f"cliopatria-record-{key}"
            claim_id = f"cliopatria-claim-{key}"
            locator = f"{release}: {name}, {start} to {end} (Wikidata {qid})"
            area = props.get("Area")
            notes = RATIONALE + (f" Reported area {round(area):,} km2." if isinstance(area, (int, float)) else "")

            datasets["source_records"].append(SourceRecord(
                id=record_id, feature_id=layer_id, feature_kind="civilization_layer",
                feature_label=name, title=f"Cliopatria: {name}", citation=f"{citation} {locator}",
                link=REPOSITORY, source_namespace=self.namespace, confidence="low",
                review_status="needs_review", notes=notes,
                valid_from_year=start, valid_to_year=end,
            ).model_dump(mode="json"))
            datasets["claims"].append(HistoricalClaim(
                id=claim_id, claim_type="supports_boundary", predicate="territorial_extent",
                subject_id=layer_id, subject_kind="civilization_layer",
                object_id=civilization_id, object_kind="civilization", source_id=source_id,
                citation_locator=locator, confidence_rationale=RATIONALE, confidence="low",
                review_status="needs_review", notes=notes,
                valid_from_year=start, valid_to_year=end, source_record_ids=[record_id],
            ).model_dump(mode="json"))
            try:
                layer = CivilizationLayer(
                    id=layer_id, civilization_id=civilization_id, name=f"{name} (Cliopatria)",
                    layer_type="source_reported_extent", variant_group=target["variant_group"],
                    interpretation_label=f"Cliopatria (Seshat) {release}",
                    interpretation_kind="boundary_variant", is_primary=False, display_order=10,
                    valid_from_year=start, valid_to_year=end, geometry_json=feature.get("geometry"),
                    is_placeholder=False, confidence="low", review_status="needs_review",
                    source_note=notes, created_at=retrieved_at, updated_at=retrieved_at,
                    source_record_ids=[record_id], claim_ids=[claim_id],
                ).model_dump(mode="json")
            except ValueError as error:
                raise ValueError(f"{qid}: invalid geometry or dates: {error}") from error
            datasets["layers"].append(layer)
            evidence = EvidenceLink(
                id=f"cliopatria-evidence-{key}", source_id=source_id, entity_type="civilization_layer",
                entity_id=layer_id, claim_type="supports_boundary", confidence_level="low",
                quote_or_note=RATIONALE, created_at=retrieved_at, updated_at=retrieved_at,
            ).model_dump(mode="json")
            evidence["review_status"] = "needs_review"
            datasets["evidence"].append(evidence)
        return NormalizedSnapshot(datasets, omissions, selected_ids=sorted(wanted))
