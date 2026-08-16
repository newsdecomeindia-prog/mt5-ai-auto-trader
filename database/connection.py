from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
from config import settings
from database.models import Base
from core import get_logger

logger = get_logger("database")


class DatabaseManager:
    def __init__(self, db_url: str = settings.DATABASE_URL):
        self.db_url = db_url
        # SQLite specific connect_args
        connect_args = {"check_same_thread": False} if self.db_url.startswith("sqlite") else {}
        self.engine = create_engine(self.db_url, connect_args=connect_args, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def init_db(self) -> None:
        """Creates all database tables if they do not exist."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Context manager for managing database sessions safely."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session rollback due to error: {e}")
            raise
        finally:
            session.close()


db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database sessions."""
    session = db_manager.SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
