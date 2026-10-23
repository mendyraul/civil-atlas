"""Report original, imported source geometry for editorial inspection; never publishes."""
import json
from sqlalchemy import text
from app.db.session import session_scope


def audit():
    with session_scope() as session:
        rows = session.execute(text("""
          SELECT l.id, l.civilization_id, ST_IsValid(l.geom) AS valid,
                 ST_IsValidReason(l.geom) AS reason, ST_NPoints(l.geom) AS vertices,
                 ST_AsGeoJSON(ST_Envelope(l.geom)) AS envelope,
                 a.payload->'source_record_ids' AS source_records,
                 a.payload->>'review_status' AS review_status,
                 a.payload->>'manifest_sha256' AS import_manifest
          FROM civilization_layers l JOIN atlas_entities a
            ON a.entity_type='layers' AND a.external_id=l.id
          WHERE l.id LIKE 'cliopatria-%' ORDER BY l.id
        """)).mappings().all()
        return [dict(row) for row in rows]


if __name__ == '__main__':
    print(json.dumps({'note': 'Topology checks do not establish historical accuracy. Original geometry is unchanged; historical/geographic fit requires editorial inspection.', 'layers': audit()}, indent=2))
