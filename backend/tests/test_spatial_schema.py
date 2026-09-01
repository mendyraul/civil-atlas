import os

import pytest
from sqlalchemy import create_engine, text


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://civil_atlas:civil_atlas@localhost:5432/civil_atlas",
)


def _database_engine():
    engine = create_engine(DATABASE_URL)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as error:  # local unit runs do not require Docker
        engine.dispose()
        pytest.skip(f"PostgreSQL is not available: {error}")
    return engine


def test_postgis_geometry_columns_support_spatial_predicates():
    engine = _database_engine()
    try:
        with engine.connect() as connection:
            assert connection.execute(text("SELECT postgis_version()")).scalar_one()
            column_types = dict(
                connection.execute(
                    text(
                        """
                        SELECT table_name, udt_name
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND column_name = 'geom'
                          AND table_name IN ('civilization_layers', 'places', 'civilization_edges')
                        """
                    )
                ).all()
            )
            assert column_types == {
                "civilization_layers": "geometry",
                "places": "geometry",
                "civilization_edges": "geometry",
            }

            connection.rollback()
            transaction = connection.begin()
            try:
                connection.execute(
                    text(
                        """
                        INSERT INTO civilizations
                          (id, slug, name, type, start_year, end_year, description,
                           display_color, confidence_level, review_status)
                        VALUES ('spatial-test-civ', 'spatial-test-civ', 'Spatial test', 'polity',
                                0, 100, 'test', '#000000', 'high', 'reviewed')
                        """
                    )
                )
                connection.execute(
                    text(
                        """
                        INSERT INTO civilization_layers
                          (id, civilization_id, name, layer_type, valid_from_year,
                           valid_to_year, geometry_json, geom, confidence_level,
                           review_status, source_note)
                        VALUES (
                          'spatial-test-layer', 'spatial-test-civ', 'Test extent', 'extent',
                          0, 100,
                          CAST(:geojson AS jsonb),
                          ST_SetSRID(ST_GeomFromGeoJSON(:geojson), 4326),
                          'high', 'reviewed', 'test'
                        )
                        """
                    ),
                    {
                        "geojson": '{"type":"Polygon","coordinates":[[[-1,-1],[1,-1],[1,1],[-1,1],[-1,-1]]]}',
                    },
                )
                assert connection.execute(
                    text(
                        """
                        SELECT ST_Intersects(
                          geom,
                          ST_SetSRID(ST_Point(0, 0), 4326)
                        )
                        FROM civilization_layers
                        WHERE id = 'spatial-test-layer'
                        """
                    )
                ).scalar_one() is True
            finally:
                transaction.rollback()
    finally:
        engine.dispose()
