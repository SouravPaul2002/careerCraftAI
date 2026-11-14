from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base

from app.config.settings import settings

# SQLAlchemy 2.1 defaults "postgresql://" to psycopg v3; use our installed psycopg2 driver
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

# Create the SQLAlchemy engine using the PostgreSQL URL from .env
# pool_pre_ping=True checks that the connection is alive before using it
engine = create_engine(database_url, pool_pre_ping=True)

# Base class that all database table models will inherit from
Base = declarative_base()


def create_tables():
    """Create all database tables defined by models inheriting from Base."""
    Base.metadata.create_all(bind=engine)


def test_connection() -> bool:
    """Run a simple query to confirm PostgreSQL is reachable."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True
