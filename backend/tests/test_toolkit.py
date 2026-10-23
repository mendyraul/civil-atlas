"""Synthetic geometries test mechanics, never historical accuracy."""
from copy import deepcopy
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.toolkit import Annotation, EpisodePack, ResearchArea, ResearchQuery
from app.services import research
from app.services.episodes import validate_episode, public_episodes
from app.services.repository import AtlasRepository
from app.seed import catalog
from app.ingestion.episodes import EpisodeAdapter
from tests.test_pleiades import database  # noqa: F401


@pytest.fixture
def toolkitdb(database, monkeypatch):
    monkeypatch.setattr(research, 'session_scope', database)
    return database


def pack():
    return EpisodePack.model_validate(dict(schema_version=1, id='synthetic-episode', title='Synthetic episode test', summary='Tests mechanics only', dataset_version='test-v1', attribution='Synthetic test fixture', steps=[dict(id='one', title='Step', narrative='Synthetic', year=117, camera=dict(center=[0, 0], zoom=2), layer_ids=['toolkit-layer'], source_record_ids=['toolkit-source'])]))


@pytest.mark.parametrize('value', [dict(bbox=[-181, 0, 0, 1]), dict(center=[0, 0]), dict(bbox=[0, 0, 1, 1], center=[0, 0], radius_km=2), dict(bbox=[0, 0, 1, 1], radius_km=2)])
def test_invalid_areas(value):
    with pytest.raises(ValueError): ResearchArea.model_validate(value)


def test_annotation_and_pack_validation():
    with pytest.raises(ValueError):
        Annotation(id='x', title='x', valid_from_year=117, valid_to_year=117, kind='territory', geometry={'type': 'Point', 'coordinates': [0, 0]})
    data = pack().model_dump()
    data['steps'][0]['asset_ids'] = ['missing']
    with pytest.raises(ValueError): EpisodePack.model_validate(data)
    normalized = EpisodeAdapter().normalize(pack().model_dump_json().encode(), [], 'v2', '2026-10-23T18:00:00Z')
    assert normalized.datasets['episodes'][0]['review_status'] == 'needs_review'
    assert normalized.datasets['episodes'][0]['dataset_version'] == 'v2'


def install_geometry(scope):
    with scope() as session:
        repo = AtlasRepository(session)
        civ = catalog.CIVILIZATIONS[0].model_dump(mode='json')
        repo.upsert('civilizations', civ['id'], civ, 'test:toolkit', published=True)
        repo.upsert_spatial_projection('civilizations', civ)
        layer = deepcopy(catalog.CIVILIZATION_LAYERS[0].model_dump(mode='json'))
        layer.update(id='toolkit-layer', civilization_id=civ['id'], review_status='reviewed', valid_from_year=100, valid_to_year=150, is_placeholder=False, geometry_placeholder=None, source_record_ids=['toolkit-source'], geometry_json={'type': 'Polygon', 'coordinates': [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]], [[3, 3], [3, 7], [7, 7], [7, 3], [3, 3]]]})
        repo.upsert('layers', layer['id'], layer, 'test:toolkit', published=True)
        repo.upsert_spatial_projection('layers', layer)
        source = dict(id='toolkit-source', feature_id=layer['id'], title='Synthetic source', citation='Synthetic geometry for tests', review_status='reviewed', confidence='low', valid_from_year=100, valid_to_year=150)
        repo.upsert('source_records', source['id'], source, 'test:toolkit', published=True)
        for name, longitude, published in [('east', 179, True), ('west', -179, True), ('private', 178, False)]:
            node = deepcopy(catalog.ATLAS_NODES[0].model_dump(mode='json'))
            node.update(id=f'toolkit-{name}', slug=f'toolkit-{name}', coordinates=[longitude, 0], start_year=100, end_year=150)
            repo.upsert('nodes', node['id'], node, 'test:toolkit', published=published)
            repo.upsert_spatial_projection('nodes', node)


def test_spatial_holes_dateline_radius_time_and_pagination(toolkitdb):
    install_geometry(toolkitdb)
    hole = research.execute_query(ResearchQuery(area=ResearchArea(bbox=[4, 4, 6, 6]), kinds=['layers']))
    assert not any(i['record']['id'] == 'toolkit-layer' for i in hole['items'])
    land = research.execute_query(ResearchQuery(area=ResearchArea(bbox=[0.5, 0.5, 1, 1]), kinds=['layers']))
    assert any(i['record']['id'] == 'toolkit-layer' for i in land['items'])
    area = ResearchArea(bbox=[170, -1, -170, 1])
    result = research.execute_query(ResearchQuery(area=area, kinds=['nodes'], page_size=1))
    assert result['total'] == 2 and len(result['items']) == 1
    second = research.execute_query(ResearchQuery(area=area, kinds=['nodes'], page=2, page_size=1))
    assert second['items'][0]['record']['id'] != result['items'][0]['record']['id']
    radius = research.execute_query(ResearchQuery(area=ResearchArea(center=[179, 0], radius_km=1), kinds=['nodes']))
    assert [i['record']['id'] for i in radius['items']] == ['toolkit-east']
    old = research.execute_query(ResearchQuery(year=99, area=area, kinds=['nodes']))
    assert old['total'] == 0
    for endpoint in [100, 150]:
        assert research.execute_query(ResearchQuery(year=endpoint, area=area, kinds=['nodes']))['total'] == 2


def test_publication_and_dependency_withdrawal(toolkitdb):
    install_geometry(toolkitdb)
    episode = pack()
    with toolkitdb() as session:
        repo = AtlasRepository(session)
        validate_episode(episode, repo)
        repo.upsert('episodes', episode.id, episode.model_dump(), 'test:toolkit')
        assert episode.id not in {p.id for p in public_episodes(repo)}
        repo.update_review_status('episodes', episode.id, 'reviewed', 'test:toolkit')
        assert episode.id in {p.id for p in public_episodes(repo)}
        repo.update_review_status('layers', 'toolkit-layer', 'needs_review', 'test:toolkit')
        assert episode.id not in {p.id for p in public_episodes(repo)}
        with pytest.raises(ValueError): validate_episode(episode, repo)


def test_http_matches_shared_service_and_cannot_reveal_private_data(toolkitdb):
    install_geometry(toolkitdb)
    query = ResearchQuery(area=ResearchArea(bbox=[170, -1, -170, 1]), kinds=['nodes'])
    expected = research.execute_query(query)
    response = TestClient(app).post('/api/v1/research/query', json=query.model_dump(mode='json'))
    assert response.status_code == 200
    assert response.json() == expected
    assert 'toolkit-private' not in response.text
    assert TestClient(app).post('/api/v1/research/query', json={'operation': 'entities_in_area', 'year': 9999}).status_code == 422


def test_mcp_uses_identical_read_only_service(toolkitdb):
    pytest.importorskip('mcp')
    from app.mcp_server import historical_research
    install_geometry(toolkitdb)
    query = ResearchQuery(operation='sources_for_feature', feature_id='toolkit-layer')
    assert historical_research(query) == research.execute_query(query)
    assert historical_research(query)['items'][0]['id'] == 'toolkit-source'


def test_event_scope_and_missing_geography_are_reported_separately(toolkitdb):
    with toolkitdb() as session:
        repo = AtlasRepository(session)
        for identifier, geometry in [('toolkit-located-event', {'type': 'Polygon', 'coordinates': [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]}), ('toolkit-unlocated-event', None)]:
            event = deepcopy(catalog.HISTORICAL_EVENTS[0].model_dump(mode='json'))
            event.update(id=identifier, start_year=117, end_year=117, geographic_scope=geometry, place_ids=[])
            repo.upsert('events', identifier, event, 'test:toolkit', published=True)
    result = research.execute_query(ResearchQuery(operation='events_in_area', area=ResearchArea(bbox=[-1, -1, 2, 2])))
    assert any(item['record']['id'] == 'toolkit-located-event' for item in result['items'])
    assert all(item['record']['id'] != 'toolkit-unlocated-event' for item in result['items'])
    assert result['unlocated_count'] >= 1


def test_episode_rejects_a_withdrawn_release(toolkitdb):
    install_geometry(toolkitdb)
    with toolkitdb() as session:
        repo = AtlasRepository(session)
        source = repo.get('source_records', 'toolkit-source')
        source['import_job_id'] = 'toolkit-source-job'
        repo.upsert('source_records', 'toolkit-source', source, 'test:toolkit', published=True)
        with pytest.raises(ValueError, match='release'): validate_episode(pack(), repo)
        repo.upsert('sources', 'toolkit-release', {'id': 'toolkit-release', 'import_job_id': 'toolkit-source-job', 'review_status': 'reviewed'}, 'test:toolkit', published=True)
        validate_episode(pack(), repo)
        # Reimporting the same release for another date updates its job metadata,
        # but the original episode still cites the same published source.
        repo.upsert('evidence', 'toolkit-evidence', {'id': 'toolkit-evidence', 'entity_id': 'toolkit-layer', 'source_id': 'toolkit-release'}, 'test:toolkit', published=True)
        repo.upsert('sources', 'toolkit-release', {'id': 'toolkit-release', 'import_job_id': 'later-source-job', 'review_status': 'reviewed'}, 'test:toolkit', published=True)
        validate_episode(pack(), repo)
        repo.update_review_status('sources', 'toolkit-release', 'rejected', 'test:toolkit')
        with pytest.raises(ValueError, match='release'): validate_episode(pack(), repo)
