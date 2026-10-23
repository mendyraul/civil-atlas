"""Validate curated episode dependencies on every public read and publication."""
from app.schemas.toolkit import Annotation, EpisodePack


def reviewed_record(repository, kind, identifier, year=None):
    record = repository.get(kind, identifier)
    if not record or record.get("review_status") != "reviewed":
        raise ValueError(f"{kind}/{identifier} must be published and reviewed")
    start, end = record.get("start_year", record.get("valid_from_year")), record.get("end_year", record.get("valid_to_year"))
    if year is not None and (start is not None and year < start or end is not None and year > end):
        raise ValueError(f"{kind}/{identifier} is not valid in {year}")
    if kind == "source_records" and record.get("import_job_id"):
        # A release can be reused by later imports (for example another year).
        # Follow its stable evidence identity before falling back to job metadata.
        source_ids = {link["source_id"] for link in repository.list("evidence")
                      if link.get("entity_id") == record.get("feature_id") and link.get("source_id")}
        releases = ([repository.get("sources", identifier) for identifier in source_ids]
                    if source_ids else [source for source in repository.list("sources")
                                        if source.get("import_job_id") == record["import_job_id"]])
        if not releases or any(not source or source.get("review_status") != "reviewed" for source in releases):
            raise ValueError("The cited source release must remain published and reviewed")
    if kind == "layers":
        if record.get("is_placeholder") or record.get("geometry_placeholder"):
            raise ValueError("Curated territory cannot use placeholder boundaries")
        if not record.get("source_record_ids"):
            raise ValueError("Curated boundaries require source records")
        for source in record["source_record_ids"]:
            reviewed_record(repository, "source_records", source, year)
    return record


def validate_annotation(annotation: Annotation, repository):
    if not annotation.source_record_ids:
        raise ValueError("Curated annotations require citations")
    for year in {annotation.valid_from_year, annotation.valid_to_year}:
        for source in annotation.source_record_ids:
            reviewed_record(repository, "source_records", source, year)
        if annotation.boundary_layer_id:
            reviewed_record(repository, "layers", annotation.boundary_layer_id, year)


def validate_episode(pack: EpisodePack, repository):
    for annotation in pack.annotations:
        record = reviewed_record(repository, "annotations", annotation.id)
        canonical = Annotation.model_validate({k: v for k, v in record.items() if k in Annotation.model_fields or k in {f.alias for f in Annotation.model_fields.values()}})
        if canonical.model_dump(exclude={"review_status"}) != annotation.model_dump(exclude={"review_status"}):
            raise ValueError("Episode annotation differs from its reviewed record")
        validate_annotation(annotation, repository)
    for step in pack.steps:
        if not step.source_record_ids:
            raise ValueError(f"Step {step.id} requires citations")
        for identifier in step.source_record_ids:
            reviewed_record(repository, "source_records", identifier, step.year)
        for identifier in step.layer_ids:
            reviewed_record(repository, "layers", identifier, step.year)
        for identifier in step.entity_ids:
            if not any(repository.get(kind, identifier) for kind in ("civilizations", "nodes", "routes", "events")):
                raise ValueError(f"Step {step.id} references missing public entity {identifier}")
        for annotation in pack.annotations:
            if annotation.id in step.annotation_ids and not annotation.valid_from_year <= step.year <= annotation.valid_to_year:
                raise ValueError("Annotation is outside the step's date")


def pack_from_record(record):
    return EpisodePack.model_validate({key: value for key, value in record.items() if key in EpisodePack.model_fields})


def public_episodes(repository):
    packs = []
    for record in repository.list("episodes"):
        try:
            pack = pack_from_record(record)
            if pack.review_status == "reviewed":
                validate_episode(pack, repository)
                for annotation in pack.annotations:
                    annotation.review_status = 'reviewed'
                packs.append(pack)
        except ValueError:
            continue  # Revoked dependencies withdraw the derived public pack immediately.
    return packs
