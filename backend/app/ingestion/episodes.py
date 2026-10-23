"""Pure episode normalization. Curated annotations are separately reviewable records."""
import json
from app.ingestion.pleiades import NormalizedSnapshot
from app.schemas.toolkit import EpisodePack


class EpisodeAdapter:
    namespace = "episodes"
    version = "1"
    label = "Curated historical episode"
    license = "ODbL-1.0"
    source_type = "curated_episode"

    def entity_ids_for(self, external_id):
        return [("episodes", external_id)]

    def normalize(self, raw, ids, dataset_version, retrieved_at):
        if len(raw) > 32 * 1024 * 1024:
            raise ValueError("Episode exceeds 32 MiB")
        pack = EpisodePack.model_validate(json.loads(raw))
        if ids and ids != [pack.id]:
            raise ValueError("Selection must name the episode ID")
        pack.dataset_version = dataset_version
        pack.review_status = "needs_review"
        for annotation in pack.annotations:
            annotation.review_status = "needs_review"
        return NormalizedSnapshot({
            "source_records": [],
            "annotations": [a.model_dump(mode="json") for a in pack.annotations],
            "episodes": [pack.model_dump(mode="json")],
        }, [], [pack.id])
