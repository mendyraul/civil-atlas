from app.seed.coverage import COVERAGE_PACKS


def test_coverage_registry_is_directional_versioned_and_reviewable():
    assert len(COVERAGE_PACKS) >= 4
    assert {pack.direction for pack in COVERAGE_PACKS} >= {"west", "east", "south", "north"}
    assert all(pack.regions and pack.era_ids and pack.focal_years for pack in COVERAGE_PACKS)
    assert all(pack.maturity and pack.coverage_tier and pack.review_status for pack in COVERAGE_PACKS)
    assert all(pack.load_strategy.startswith("load_at_") for pack in COVERAGE_PACKS)
