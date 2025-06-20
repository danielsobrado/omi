# backend/database/postgres/client.py
import os
import logging
from functools import wraps
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base

POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://user:password@localhost:5432/omi_db")

engine = create_engine(POSTGRES_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# In a real app, this would be configured globally from a config file.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_session():
    """Get a database session for direct use"""
    return SessionLocal()

def db_session_manager(func):
    """
    A decorator to manage database sessions. It handles commits, rollbacks,
    and closing the session. It re-raises database errors to be handled by the caller.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = get_db_session()
        try:
            # Pass the session as the first argument to the decorated function
            result = func(session, *args, **kwargs)
            session.commit()
            return result
        except SQLAlchemyError as e:
            logging.error(f"Database error in {func.__name__}: {e}", exc_info=True)
            session.rollback()
            # Re-raise the exception to be handled by a higher-level error handler
            raise
        finally:
            session.close()
    return wrapper