"""Public, date-filtered civilization context with publication-gated dependencies."""

from app.db.session import session_scope
from app.services.repository import AtlasRepository


def civilization_context(civilization_id, year):
    result = {"leaders": [], "capitals": []}
    with session_scope() as session:
        repo = AtlasRepository(session)
        civilization = repo.get("civilizations", civilization_id)

        def active(record):
            start = record.get("start_year", record.get("valid_from_year"))
            end = record.get("end_year", record.get("valid_to_year"))
            return (start is None or start <= year) and (end is None or year <= end)

        if not civilization or not active(civilization):
            return result

        def supported(record):
            return (
                bool(record.get("source_record_ids"))
                and all(
                    (source := repo.get("source_records", rid)) and active(source)
                    for rid in record["source_record_ids"]
                )
                and bool(repo.get("sources", record.get("source_id", "")))
            )

        for kind, target in [("offices", "leaders"), ("capital_roles", "capitals")]:
            for record in repo.list(kind):
                if (
                    record["civilization_id"] != civilization_id
                    or not record["start_year"] <= year <= record["end_year"]
                    or not supported(record)
                ):
                    continue
                related = repo.get(
                    "people" if kind == "offices" else "places",
                    record["person_id" if kind == "offices" else "place_id"],
                )
                if not related or not active(related):
                    continue
                if kind == "offices" and not all(
                    repo.get("source_records", rid)
                    for rid in related.get("source_record_ids", [])
                ):
                    continue
                result[target].append(
                    {
                        "id": record["id"],
                        "label": related.get("name", related.get("canonical_name")),
                        "start_year": record["start_year"],
                        "end_year": record["end_year"],
                        "citation": record["statement"],
                    }
                )
    return result
