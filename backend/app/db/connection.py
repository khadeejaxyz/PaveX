"""
PaveX Database Connection Layer
SQLAlchemy + PostgreSQL + PostGIS
"""

import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv
import logging

# Configure logging
logger = logging.getLogger(__name__)

# ============================================
# DATABASE CONFIGURATION
# ============================================

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# Load from environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "pavex")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Construct database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.bjztzzunicqnyyfkrpuf:9h#wddKpS9C8,w*@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres",
)

# ============================================
# ENGINE CONFIGURATION
# ============================================

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    future=True,
    poolclass=QueuePool,
    pool_size=10,  # Maximum number of connections to keep open
    max_overflow=20,  # Maximum number of connections to create beyond pool_size
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False,  # Set to True for SQL query logging (development only)
)

# ============================================
# SESSION CONFIGURATION
# ============================================

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,  # Disable autocommit for explicit transaction control
    autoflush=False,  # Disable autoflush for better control
    bind=engine
)

# Base class for ORM models
Base = declarative_base()

# ============================================
# DEPENDENCY INJECTION
# FastAPI database session dependency
# ============================================

def get_db():
    """
    Database session dependency for FastAPI endpoints.
    
    Yields:
        Session: SQLAlchemy database session
        
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db session here
            pass
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================
# CONNECTION UTILITIES
# ============================================

def init_db():
    """
    Initialize database connection.
    Verifies connection and logs status.
    
    Raises:
        Exception: If connection fails
    """
    try:
        # Test connection
        with engine.connect() as connection:
            logger.info("✓ Database connection successful")
            logger.info(f"✓ Connected to: {DB_HOST}:{DB_PORT}/{DB_NAME}")
            
            # Verify PostGIS extension
            result = connection.execute(text("SELECT PostGIS_Version();"))
            version = result.fetchone()
            if version:
                logger.info(f"✓ PostGIS extension enabled: {version[0]}")
            else:
                logger.warning("⚠ PostGIS extension not found")
                
    except Exception as e:
        logger.error(f"✗ Database connection failed: {str(e)}")
        raise

def close_db():
    """
    Close database connection and cleanup resources.
    """
    try:
        engine.dispose()
        logger.info("✓ Database connection closed")
    except Exception as e:
        logger.error(f"✗ Error closing database: {str(e)}")

# ============================================
# HEALTH CHECK
# ============================================

def check_db_health():
    """
    Check database health status.
    
    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False
