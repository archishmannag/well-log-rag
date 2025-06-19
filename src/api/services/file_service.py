from typing import List, Dict, Any, Optional
import logging
from functools import lru_cache
import time

from src.api.db.database import Database
from src.api.schemas.witsml import FileInfo, FileResponse, FileContent

logger = logging.getLogger(__name__)


class FileService:
    """Service for interacting with WITSML files in the database."""

    def __init__(self):
        self.db = Database()
        # Cache expiry time in seconds
        self.cache_ttl = 300
        # Store cache timestamps for manual TTL management
        self._cache_timestamps = {}

    def list_files(
        self, well_name: Optional[str] = None, file_type: Optional[str] = None
    ) -> List[FileInfo]:
        """
        List available WITSML files with optional filtering.

        Args:
            well_name: Optional filter by well name
            file_type: Optional filter by file type

        Returns:
            List of FileInfo objects
        """
        cache_key = f"list_files:{well_name}:{file_type}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for {cache_key}")
            return cached_result

        try:
            # Build query conditions
            conditions = {}
            if well_name:
                conditions["well_name"] = well_name
            if file_type:
                conditions["file_type"] = file_type

            # Get files from database
            files_data = self.db.query_files(conditions)

            # Convert to FileInfo objects
            result = [
                FileInfo(
                    file_id=file["id"],
                    well_name=file["well_name"],
                    file_type=file["file_type"],
                    file_size=file["size"],
                    created_at=file["created_at"],
                    updated_at=file["updated_at"],
                    metadata=file.get("metadata", {}),
                )
                for file in files_data
            ]

            # Cache the result
            self._add_to_cache(cache_key, result)

            return result
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            raise

    def get_file(self, file_id: str) -> Optional[FileResponse]:
        """
        Retrieve a specific WITSML file by ID.

        Args:
            file_id: Unique identifier for the file

        Returns:
            FileResponse object if found, None otherwise
        """
        cache_key = f"get_file:{file_id}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for {cache_key}")
            return cached_result

        try:
            # Get file metadata
            file_metadata = self.db.get_file_metadata(file_id)
            if not file_metadata:
                return None

            # Get file content
            file_content = self.db.get_file_content(file_id)

            # Create response
            info = FileInfo(
                file_id=file_metadata["id"],
                well_name=file_metadata["well_name"],
                file_type=file_metadata["file_type"],
                file_size=file_metadata["size"],
                created_at=file_metadata["created_at"],
                updated_at=file_metadata["updated_at"],
                metadata=file_metadata.get("metadata", {}),
            )

            content = FileContent(
                header=file_content["header"], data=file_content["data"]
            )

            result = FileResponse(info=info, content=content)

            # Cache the result
            self._add_to_cache(cache_key, result)

            return result
        except Exception as e:
            logger.error(f"Error retrieving file {file_id}: {str(e)}")
            raise

    # Cache management methods
    def _add_to_cache(self, key: str, value: Any):
        """Add a value to the cache with current timestamp."""
        self._cache[key] = value
        self._cache_timestamps[key] = time.time()

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get a value from cache if it exists and is not expired."""
        if key in self._cache:
            timestamp = self._cache_timestamps.get(key, 0)
            if time.time() - timestamp < self.cache_ttl:
                return self._cache[key]
            else:
                # Expired cache entry
                del self._cache[key]
                del self._cache_timestamps[key]
        return None

    # Cache storage
    _cache = {}

    # Additional method for cache management
    def clear_cache(self):
        """Clear all cached data."""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("File service cache cleared")

    def query_files(self, query_params: Dict[str, Any]) -> List[FileInfo]:
        """
        Query WITSML files based on advanced criteria.

        Args:
            query_params: Dictionary of query parameters

        Returns:
            List of FileInfo objects matching the query
        """
        try:
            # Process query parameters
            conditions = {}

            if query_params.get("well_names"):
                conditions["well_name"] = {"$in": query_params["well_names"]}

            if query_params.get("file_types"):
                conditions["file_type"] = {"$in": query_params["file_types"]}

            if query_params.get("date_range"):
                date_range = query_params["date_range"]
                if "start" in date_range:
                    conditions["created_at"] = {"$gte": date_range["start"]}
                if "end" in date_range:
                    if "created_at" in conditions:
                        conditions["created_at"]["$lte"] = date_range["end"]
                    else:
                        conditions["created_at"] = {"$lte": date_range["end"]}

            # Add metadata filters
            if query_params.get("metadata_filters"):
                for key, value in query_params["metadata_filters"].items():
                    conditions[f"metadata.{key}"] = value

            # Execute query
            files_data = self.db.query_files(conditions)

            # Convert to FileInfo objects
            return [
                FileInfo(
                    file_id=file["id"],
                    well_name=file["well_name"],
                    file_type=file["file_type"],
                    file_size=file["size"],
                    created_at=file["created_at"],
                    updated_at=file["updated_at"],
                    metadata=file.get("metadata", {}),
                )
                for file in files_data
            ]
        except Exception as e:
            logger.error(f"Error querying files: {str(e)}")
            raise
