import json
import pytest
from app.ingestion.ohm import OHMAdapter
from app.ingestion.licenses import check_license


def snapshot(**tags):
    ring = [[0,0],[4,0],[4,4],[0,4],[0,0]]
    def member(points, role='outer'):
        return {'type':'way','role':role,'geometry':[{'lon':x,'lat':y} for x,y in points]}
    return {'elements':[{'type':'relation','id':1,'tags':{'name':'Test Roman boundary','wikidata':'Q12544',
        'start_date':'0117-01-01','end_date':'0118-01-01','fixme:s':'needs source',**tags},
        'members':[member(ring[:3]),member(ring[2:]),member([[1,1],[2,1],[2,2],[1,2],[1,1]],'inner')]}]}


def normalize(data, ids=None):
    return OHMAdapter(117).normalize(json.dumps(data).encode(), ids or [], 'test-v1','2026-11-05T15:00:00Z')


def test_boundary_holes_provenance_and_private_reading():
    check_license(OHMAdapter(117))
    result = normalize(snapshot())
    layer = result.datasets['layers'][0]
    assert len(layer['geometry_json']['coordinates'][0]) == 2
    assert layer['variant_group'] == 'roman-117-frontier-readings'
    assert layer['is_primary'] is False
    assert 'needs source' in layer['source_note']
    for records in result.datasets.values():
        assert all(r['review_status'] == 'needs_review' for r in records)


@pytest.mark.parametrize('tags', [{'license':'CC-BY-SA'}, {'wikidata':'Q999999'}, {'start_date':'~100'}, {'end_date':'0100'}])
def test_unsupported_inputs_are_explicit_omissions(tags):
    result = normalize(snapshot(**tags))
    assert not result.datasets['layers']
    assert result.omissions[0]['reason']


def test_incomplete_relation_and_missing_selection():
    data = snapshot()
    data['elements'][0]['members'].pop(1)
    result = normalize(data,['1','2'])
    assert not result.datasets['layers']
    assert {o['id'] for o in result.omissions} == {'1','2'}


def test_duplicate_relations_fail():
    data = snapshot(); data['elements'] *= 2
    with pytest.raises(ValueError, match='duplicate'):
        normalize(data)


def test_import_review_and_replay(database, tmp_path, monkeypatch):
    from app.ingestion.pipeline import prepare_import, import_bundle
    from app.services.repository import AtlasRepository
    from app.api import routes
    from app.main import app
    from fastapi.testclient import TestClient
    path = tmp_path / 'overpass.json'
    path.write_text(json.dumps(snapshot()))
    bundle = prepare_import(OHMAdapter(117),path,['1'],'ohm-test-v1','2026-11-05T15:00:00Z')
    assert import_bundle(bundle,tmp_path/'archive','test:ohm')['status'] == 'completed'
    with database() as session:
        repo = AtlasRepository(session)
        assert repo.get('layers','ohm-relation-1') is None
        assert repo.get('layers','ohm-relation-1',published_only=False)['is_primary'] is False
    monkeypatch.setattr(routes.settings,'editorial_api_key','test-key')
    client = TestClient(app)
    action = {'assignment_id':'review-layers-ohm-relation-1','decision_type':'approve',
              'reviewer':'test:reviewer','rationale':'Synthetic geometry reviewed for integration test.'}
    response = client.post('/api/v1/review-actions',headers={'X-Editorial-Key':'test-key'},json=action)
    assert response.status_code == 200, response.text
    assert any(l['id']=='ohm-relation-1' for l in client.get('/api/v1/world/117').json()['layers'])
    assert import_bundle(bundle,tmp_path/'archive','test:ohm')['status'] == 'duplicate'
    with database() as session:
        assert AtlasRepository(session).get('layers','ohm-relation-1')['review_status'] == 'reviewed'


from tests.test_pleiades import database  # noqa: E402,F401
