"""
Database configuration and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, Session
from typing import Generator
from app.core.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Create SessionLocal class (for backwards compatibility)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models (for backwards compatibility)
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session (legacy).
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session() -> Generator[Session, None, None]:
    """
    Dependency function that yields a SQLModel database session.

    Yields:
        Database session for use in FastAPI endpoints

    Usage:
        @app.get("/users")
        def get_users(session: Session = Depends(get_session)):
            ...
    """
    with Session(engine) as session:
        yield session


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def create_db_and_tables():
    """
    Create database tables for all SQLModel models.

    This should be called on application startup or via Alembic migrations.
    """
    SQLModel.metadata.create_all(engine)
