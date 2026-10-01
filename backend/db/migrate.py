"""
PaveX Database Migration Script
Runs schema.sql against your current DATABASE_URL.

- Safe to run on an existing database where the schema already exists
- Migrates old hazard_events data into the new hazards table if found
- Verifies the result at the end

Usage:
    python backend/db/migrate.py
"""

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("pavex_migrate")

backend_dir = Path(__file__).resolve().parents[1]
load_dotenv(backend_dir / ".env")
sys.path.insert(0, str(backend_dir))

try:
    from sqlalchemy import text

    from app.db.connection import engine
except Exception as e:
    logger.error("Could not load DB engine: %s", e)
    sys.exit(1)


SCHEMA_SQL = Path(__file__).parent / "schema.sql"


def split_sql_statements(sql: str) -> list[str]:
    """Split SQL on semicolons while preserving DO $$...$$ blocks."""
    statements = []
    current = []
    in_dollar_quote = False
    i = 0

    while i < len(sql):
        if sql.startswith("$$", i):
            in_dollar_quote = not in_dollar_quote
            current.append("$$")
            i += 2
            continue

        char = sql[i]
        current.append(char)

        if char == ";" and not in_dollar_quote:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []

        i += 1

    trailing = "".join(current).strip()
    if trailing:
        statements.append(trailing)

    return statements


def run():
    if not SCHEMA_SQL.exists():
        logger.error("schema.sql not found at %s", SCHEMA_SQL)
        sys.exit(1)

    sql = SCHEMA_SQL.read_text(encoding="utf-8")

    logger.info("=" * 60)
    logger.info("PaveX DB Migration")
    logger.info("Schema: %s", SCHEMA_SQL)
    logger.info("=" * 60)

    logger.info("Applying schema.sql ...")
    statements = split_sql_statements(sql)
    with engine.begin() as conn:
        for index, statement in enumerate(statements, start=1):
            try:
                conn.exec_driver_sql(statement)
            except Exception as e:
                logger.error("schema.sql statement %s/%s failed: %s", index, len(statements), e)
                logger.error(statement)
                sys.exit(1)
    logger.info("schema.sql applied successfully")

    with engine.connect() as conn:
        old_exists = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = current_schema()
                  AND table_name = 'hazard_events'
            )
        """)).scalar()

    if old_exists:
        logger.info("Found old hazard_events table; migrating data to hazards ...")
        migrate_sql = text("""
            INSERT INTO hazards (
                id,
                hazard_type,
                severity,
                confidence,
                latitude,
                longitude,
                recommended_speed_kmph,
                first_detected_at,
                last_detected_at,
                detection_count,
                status,
                metadata
            )
            SELECT
                id,
                CASE hazard_type
                    WHEN 'pothole' THEN 'pothole'
                    WHEN 'speed_hump' THEN 'speed_hump'
                    ELSE 'other'
                END::hazard_type_enum,
                CASE severity
                    WHEN 'low' THEN 'low'
                    WHEN 'medium' THEN 'medium'
                    WHEN 'high' THEN 'high'
                    WHEN 'critical' THEN 'critical'
                    ELSE 'low'
                END::severity_enum,
                confidence,
                latitude,
                longitude,
                speed_recommendation::real,
                captured_at,
                captured_at,
                1,
                'active',
                '{}'::jsonb
            FROM hazard_events
            ON CONFLICT (id) DO NOTHING;
        """)
        with engine.begin() as conn:
            result = conn.execute(migrate_sql)
            logger.info("Migrated %s row(s) from hazard_events to hazards", result.rowcount)
    else:
        logger.info("No old hazard_events table found; nothing to migrate")

    logger.info("Verifying ...")
    with engine.connect() as conn:
        postgis_ver = conn.execute(text("SELECT PostGIS_Version()")).scalar()
        hazard_count = conn.execute(text("SELECT COUNT(*) FROM hazards")).scalar()
        cols = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'hazards'
            ORDER BY ordinal_position
        """)).fetchall()

    logger.info("PostGIS: %s", postgis_ver)
    logger.info("hazards table: %s row(s)", hazard_count)
    logger.info("Columns: %s", ", ".join(r[0] for r in cols))
    logger.info("=" * 60)
    logger.info("Migration complete!")


if __name__ == "__main__":
    run()
