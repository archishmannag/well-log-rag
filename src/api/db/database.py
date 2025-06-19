from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    DateTime,
    JSON,
    MetaData,
    Table,
    select,
    pool,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Dict, List, Any, Optional
import logging
import time
from contextlib import contextmanager

from src.api.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()
metadata = MetaData()


class Database:
    """Database connection and query utilities for WITSML data."""

    def __init__(self):
        """Initialize database connection."""
        # Updated to use MariaDB connection string with connection pooling
        connection_string = (
            f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}@"
            f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        )
        self.engine = create_engine(
            connection_string,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_pre_ping=True,  # Verify connections before using them
        )
        self.Session = sessionmaker(bind=self.engine)
        self._initialize_tables()

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()

    def _initialize_tables(self):
        """Initialize database tables if they don't exist."""
        # Define the witsml_files table
        self.witsml_files = Table(
            "witsml_files",
            metadata,
            Column("id", String(36), primary_key=True),  # Specified length for MariaDB
            Column("well_name", String(255), nullable=False, index=True),
            Column("file_type", String(50), nullable=False, index=True),
            Column("size", Integer, nullable=False),
            Column("created_at", DateTime, nullable=False, index=True),
            Column("updated_at", DateTime, nullable=False),
            # MariaDB uses LONGTEXT for JSON data
            Column("metadata", JSON, nullable=True),
        )

        # Define the witsml_file_contents table
        self.witsml_file_contents = Table(
            "witsml_file_contents",
            metadata,
            Column("file_id", String(36), primary_key=True),
            # MariaDB uses LONGTEXT for JSON data
            Column("header", JSON, nullable=False),
            Column("data", JSON, nullable=False),
        )

        # Create tables if they don't exist
        try:
            metadata.create_all(self.engine)
            logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database tables: {str(e)}")
            raise

    def query_files(self, conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query WITSML files based on conditions.

        Args:
            conditions: Dictionary of query conditions

        Returns:
            List of file metadata dictionaries
        """
        try:
            with self.session_scope() as session:
                start_time = time.time()
                query = select(self.witsml_files)

                # Apply conditions to query
                for key, value in conditions.items():
                    if isinstance(value, dict) and "$in" in value:
                        query = query.where(self.witsml_files.c[key].in_(value["$in"]))
                    elif isinstance(value, dict) and "$gte" in value:
                        query = query.where(self.witsml_files.c[key] >= value["$gte"])
                    elif isinstance(value, dict) and "$lte" in value:
                        query = query.where(self.witsml_files.c[key] <= value["$lte"])
                    else:
                        query = query.where(self.witsml_files.c[key] == value)

                result = session.execute(query).fetchall()

                # Log query performance
                query_time = time.time() - start_time
                if query_time > 1.0:
                    logger.warning(f"Slow query (took {query_time:.2f}s): {str(query)}")

                # Convert result to dictionaries
                return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"Database query error: {str(e)}")
            raise

    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific file.

        Args:
            file_id: Unique identifier for the file

        Returns:
            Dictionary of file metadata or None if not found
        """
        try:
            with self.session_scope() as session:
                query = select(self.witsml_files).where(
                    self.witsml_files.c.id == file_id
                )
                result = session.execute(query).fetchone()

                if result:
                    return dict(result)
                return None
        except Exception as e:
            logger.error(f"Error getting file metadata for {file_id}: {str(e)}")
            raise

    def get_file_content(self, file_id: str) -> Dict[str, Any]:
        """
        Get content for a specific file.

        Args:
            file_id: Unique identifier for the file

        Returns:
            Dictionary with header and data from the file
        """
        try:
            with self.session_scope() as session:
                query = select(self.witsml_file_contents).where(
                    self.witsml_file_contents.c.file_id == file_id
                )
                result = session.execute(query).fetchone()

                if not result:
                    raise ValueError(f"Content for file {file_id} not found")

                return {"header": result.header, "data": result.data}
        except Exception as e:
            logger.error(f"Error getting file content for {file_id}: {str(e)}")
            raise

    def health_check(self) -> bool:
        """Check if database connection is healthy."""
        try:
            with self.engine.connect() as connection:
                connection.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
