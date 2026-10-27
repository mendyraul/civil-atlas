"""Publication contract shared with browser acceptance; no historical assertions."""
from copy import deepcopy
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
from app.seed import catalog
from app.services.repository import AtlasRepository
from tests.test_pleiades import database  # noqa: F401

FIXTURE = Path(__file__).parents[2] / 'frontend/acceptance/fixtures/boundary-readings.json'


def test_public_boundary_contract_requires_review_and_excludes_private_reading(database, monkeypatch):  # noqa: F811
    fixture = json.loads(FIXTURE.read_text())
    monkeypatch.setattr(routes.settings, 'editorial_api_key', 'acceptance-test-key')
    client = TestClient(app)
    headers = {'X-Editorial-Key': 'acceptance-test-key'}
    layers = fixture['world']['layers'] + [fixture['privateLayer']]
    assignments = []
    with database() as session:
        repo = AtlasRepository(session)
        civilization = fixture['world']['civilizations'][0]
        repo.upsert('civilizations', civilization['id'], civilization, 'test:acceptance', published=True)
        for kind, records in [('source_records', fixture['sources']), ('layers', layers)]:
            for record in records:
                proposed = {**record, 'review_status': 'needs_review'}
                repo.upsert(kind, record['id'], proposed, 'test:acceptance', published=False)
                if kind == 'layers':
                    repo.upsert_spatial_projection(kind, proposed)
                assignment = deepcopy(catalog.REVIEW_ASSIGNMENTS[0].model_dump(mode='json'))
                assignment.update(id=f'acceptance-review-{record["id"]}', entity_type=kind,
                                  entity_id=record['id'], current_review_status='needs_review',
                                  target_review_status='reviewed')
                repo.upsert('review_assignments', assignment['id'], assignment, 'test:acceptance')
                if record['id'] != fixture['privateLayer']['id']:
                    assignments.append(assignment['id'])

    def public_readings():
        world = client.get('/api/v1/world/117')
        assert world.status_code == 200
        return [layer for layer in world.json()['layers'] if layer['id'].startswith('acceptance-')]

    assert public_readings() == []
    assert not any(source['id'].startswith('acceptance-') for source in client.get('/api/v1/sources').json())
    assert client.get('/api/v1/review-assignments').status_code == 401
    for assignment_id in assignments:
        response = client.post('/api/v1/review-actions', headers=headers, json={
            'assignment_id': assignment_id, 'decision_type': 'approve',
            'reviewer': 'test:acceptance', 'rationale': 'Synthetic contract acceptance only; not historical evidence.',
        })
        assert response.status_code == 200, response.text
    assert sorted(public_readings(), key=lambda layer: layer['id']) == sorted(fixture['world']['layers'], key=lambda layer: layer['id'])
    sources = client.get('/api/v1/sources').json()
    assert sorted((source for source in sources if source['id'].startswith('acceptance-')), key=lambda source: source['id']) == sorted(fixture['sources'], key=lambda source: source['id'])
    assert fixture['privateLayer']['id'] not in client.get('/api/v1/spatial/layers', params={'year': 117}).text
