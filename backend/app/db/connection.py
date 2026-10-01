"""
PaveX Database Connection Layer
SQLAlchemy + PostgreSQL + PostGIS (Supabase)
"""

import os
import logging
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# ============================================
# DATABASE CONFIGURATION
# ============================================
# DATABASE_URL is REQUIRED. No hardcoded fallback — a fallback credential
# in source code is a leaked secret waiting to happen. Put the real value
# only in backend/.env (which must be gitignored).

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Create backend/.env from .env.example and "
        "set your Supabase connection string there."
    )

# ============================================
# ENGINE
# ============================================

engine = create_engine(
    DATABASE_URL,
    future=True,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,   # detects and drops dead connections before use
    pool_recycle=1800,    # Supabase poolers can drop idle connections; recycle at 30 min
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============================================
# FASTAPI DEPENDENCY
# ============================================

def get_db():
    """
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================
# STARTUP / HEALTH UTILITIES
# ============================================

def init_db():
    """Call once at FastAPI startup. Raises if the DB is unreachable."""
    with engine.connect() as connection:
        logger.info("Database connection successful")

        result = connection.execute(text("SELECT PostGIS_Version();"))
        version = result.fetchone()
        if version:
            logger.info(f"PostGIS enabled: {version[0]}")
        else:
            logger.warning("PostGIS extension not detected — spatial queries will fail")


def check_db_health() -> bool:
    """Used by GET /health. Returns True/False, never raises."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def close_db():
    engine.dispose()
    logger.info("Database connections closed")