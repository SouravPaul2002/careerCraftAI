from sqlalchemy.orm import sessionmaker

from app.database.connection import engine

# SessionLocal is a factory that creates a new database session for each request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Provide a database session to a route, then close it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

