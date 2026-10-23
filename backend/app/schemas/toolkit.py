"""Versioned research and episode contracts, shared by HTTP and operator imports."""
import math
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from app.schemas import GeoJSONGeometry


class Contract(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid", allow_inf_nan=False)


class Camera(Contract):
    center: tuple[float, float]
    zoom: float = Field(default=2, ge=0, le=20)
    bearing: float = Field(default=0, ge=-180, le=180)
    pitch: float = Field(default=0, ge=0, le=60)

    @model_validator(mode="after")
    def coordinates(self):
        if not -180 <= self.center[0] <= 180 or not -85 <= self.center[1] <= 85:
            raise ValueError("camera center is out of range")
        return self


class Annotation(Contract):
    id: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=200)
    note: str = Field(default="", max_length=10000)
    valid_from_year: int = Field(ge=-600, le=1800)
    valid_to_year: int = Field(ge=-600, le=1800)
    geometry: dict | None = None
    boundary_layer_id: str | None = None
    source_record_ids: list[str] = Field(default_factory=list, max_length=100)
    kind: Literal["explanation", "territory"] = "explanation"
    review_status: Literal["needs_review", "reviewed", "rejected"] = "needs_review"
    confidence: Literal["low", "medium", "medium_high", "high"] = "low"

    @model_validator(mode="after")
    def validate_annotation(self):
        if self.valid_from_year > self.valid_to_year:
            raise ValueError("annotation years are reversed")
        if self.kind == "territory" and (not self.boundary_layer_id or self.geometry is not None):
            raise ValueError("territory annotations must reference a boundary layer, never freehand geometry")
        if not self.boundary_layer_id and not self.geometry:
            raise ValueError("annotation needs geometry or a boundary reference")
        if self.geometry:
            kind, coordinates = self.geometry.get("type"), self.geometry.get("coordinates")
            if kind in {"Polygon", "MultiPolygon"}:
                GeoJSONGeometry.model_validate(self.geometry)
            elif kind in {"Point", "LineString"}:
                points = [coordinates] if kind == "Point" else coordinates
                if not isinstance(points, list) or len(points) < (1 if kind == "Point" else 2):
                    raise ValueError("invalid annotation coordinates")
                for point in points:
                    if not isinstance(point, (list, tuple)) or len(point) != 2 or any(type(n) not in (int, float) or not math.isfinite(n) for n in point) or not -180 <= point[0] <= 180 or not -90 <= point[1] <= 90:
                        raise ValueError("invalid annotation coordinate")
            else:
                raise ValueError("unsupported annotation geometry")
        return self


class EpisodeAsset(Contract):
    id: str = Field(min_length=1, max_length=100)
    kind: Literal["image", "audio", "video"]
    path: str
    attribution: str = Field(min_length=1, max_length=2000)
    license: str = Field(min_length=1, max_length=200)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    byte_length: int = Field(gt=0, le=8 * 1024 * 1024)
    bounds: tuple[float, float, float, float] | None = None
    coordinates: tuple[float, float] | None = None

    @model_validator(mode="after")
    def placement(self):
        from app.ingestion.licenses import resolve_license
        self.license = resolve_license(self.license).spdx
        if not re.fullmatch(r"[A-Za-z0-9_-]+(?:/[A-Za-z0-9_.-]+)+", self.path) or any(p in {".", ".."} for p in self.path.split("/")):
            raise ValueError("asset path must stay inside the trusted episode-assets directory")
        extensions = {"image": (".png",), "audio": (".mp3", ".ogg", ".wav"), "video": (".mp4", ".webm")}
        if not self.path.lower().endswith(extensions[self.kind]):
            raise ValueError("asset extension does not match kind")
        if self.kind == "image":
            if not self.bounds or not (-180 <= self.bounds[0] < self.bounds[2] <= 180 and -85 <= self.bounds[1] < self.bounds[3] <= 85):
                raise ValueError("images need ordered geographic bounds")
        elif not self.coordinates or not (-180 <= self.coordinates[0] <= 180 and -90 <= self.coordinates[1] <= 90):
            raise ValueError("media needs a geographic anchor")
        return self


class EpisodeStep(Contract):
    id: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)
    narrative: str = Field(min_length=1, max_length=10000)
    year: int = Field(ge=-600, le=1800)
    camera: Camera
    entity_ids: list[str] = Field(default_factory=list, max_length=100)
    layer_ids: list[str] = Field(default_factory=list, max_length=100)
    annotation_ids: list[str] = Field(default_factory=list, max_length=100)
    asset_ids: list[str] = Field(default_factory=list, max_length=8)
    source_record_ids: list[str] = Field(default_factory=list, max_length=100)
    hold_seconds: float = Field(default=8, ge=2, le=120)


class EpisodePack(Contract):
    schema_version: Literal[1] = 1
    id: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(min_length=1, max_length=200)
    summary: str = Field(min_length=1, max_length=10000)
    dataset_version: str = Field(min_length=1, max_length=100)
    attribution: str = Field(min_length=1, max_length=2000)
    license: Literal["ODbL-1.0"] = "ODbL-1.0"
    review_status: Literal["needs_review", "reviewed", "rejected"] = "needs_review"
    steps: list[EpisodeStep] = Field(min_length=1, max_length=100)
    annotations: list[Annotation] = Field(default_factory=list, max_length=1000)
    assets: list[EpisodeAsset] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def references(self):
        for records in (self.steps, self.annotations, self.assets):
            ids = [record.id for record in records]
            if len(ids) != len(set(ids)):
                raise ValueError("duplicate IDs in episode")
        annotation_ids, asset_ids = {a.id for a in self.annotations}, {a.id for a in self.assets}
        for step in self.steps:
            if set(step.annotation_ids) - annotation_ids or set(step.asset_ids) - asset_ids:
                raise ValueError("episode step references missing content")
            if sum(a.byte_length for a in self.assets if a.id in step.asset_ids) > 32 * 1024 * 1024:
                raise ValueError("step assets exceed 32 MiB")
        return self


class ResearchArea(Contract):
    bbox: tuple[float, float, float, float] | None = None
    center: tuple[float, float] | None = None
    radius_km: float | None = Field(default=None, gt=0, le=2000)
    layer_id: str | None = None

    @model_validator(mode="after")
    def one_area(self):
        if sum(value is not None for value in (self.bbox, self.center, self.layer_id)) != 1:
            raise ValueError("choose exactly one area")
        if self.bbox and (self.bbox[0] == self.bbox[2] or not (-180 <= self.bbox[0] <= 180 and -180 <= self.bbox[2] <= 180 and -90 <= self.bbox[1] < self.bbox[3] <= 90)):
            raise ValueError("invalid bounding box")
        if self.center and (self.radius_km is None or not -180 <= self.center[0] <= 180 or not -90 <= self.center[1] <= 90):
            raise ValueError("radius area needs a valid center and radius")
        if self.radius_km is not None and self.center is None:
            raise ValueError("radius requires a center")
        return self


class ResearchQuery(Contract):
    operation: Literal["entities_in_area", "events_in_area", "compare_boundaries", "sources_for_feature", "episodes", "atlas_link"] = "entities_in_area"
    year: int = Field(default=117, ge=-600, le=1800)
    area: ResearchArea | None = None
    kinds: list[Literal["layers", "nodes", "routes", "events"]] = Field(default_factory=lambda: ["layers", "nodes", "routes"], max_length=4)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    feature_id: str | None = None
    left_layer_id: str | None = None
    right_layer_id: str | None = None
    right_year: int | None = Field(default=None, ge=-600, le=1800)
    camera: Camera | None = None

    @model_validator(mode="after")
    def requirements(self):
        if self.operation in {"entities_in_area", "events_in_area"} and self.area is None:
            raise ValueError("geographic queries require an area")
        if self.operation == "sources_for_feature" and not self.feature_id:
            raise ValueError("source lookup requires feature_id")
        if self.operation == "compare_boundaries" and not (self.left_layer_id and self.right_layer_id):
            raise ValueError("comparison requires two layer IDs")
        return self


from typing import Any
from typing_extensions import TypedDict


class ResearchResult(TypedDict):
    operation: str
    year: int
    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int
    data_version: str
    limitations: list[str]
    unlocated_count: int
    summary: str
