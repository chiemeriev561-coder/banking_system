import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()


def _get_database_url() -> str:
    """Return the configured PostgreSQL connection string."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/banking_system",
    )


SQLALCHEMY_DATABASE_URL = _get_database_url()

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Sync dependency for getting a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
