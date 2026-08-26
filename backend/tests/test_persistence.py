from datetime import UTC, datetime
from sqlalchemy import create_engine, insert, select
from app.models.tables import civilizations, metadata

def test_database_round_trip_persists_bce_dates(tmp_path):
    engine=create_engine(f"sqlite:///{tmp_path/'atlas.db'}"); metadata.create_all(engine); now=datetime.now(UTC)
    row=dict(id='fixture',slug='fixture',name='Fixture',type='polity',start_year=-550,end_year=-480,description='test',display_color='#000',confidence_level='medium',review_status='needs_review',created_at=now,updated_at=now)
    with engine.begin() as connection: connection.execute(insert(civilizations).values(**row))
    engine.dispose(); reopened=create_engine(f"sqlite:///{tmp_path/'atlas.db'}")
    with reopened.connect() as connection: assert connection.execute(select(civilizations.c.start_year).where(civilizations.c.id=='fixture')).scalar_one()==-550
