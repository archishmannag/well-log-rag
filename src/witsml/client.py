import logging
from typing import Dict, List, Any, Optional
import functools
import time
from datetime import datetime, timedelta

from src.witsml.connector import WitsmlConnector
from src.witsml.parser import WitsmlParser

logger = logging.getLogger(__name__)


class WitsmlClient:
    """
    High-level client for retrieving data from WITSML servers.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        version: Optional[str] = None,
    ):
        """
        Initialize the WITSML client.

        Args:
            url: WITSML server URL
            username: WITSML server username
            password: WITSML server password
            version: WITSML version
        """
        self.connector = WitsmlConnector(url, username, password, version)
        self.parser = WitsmlParser()

        # Cache settings
        self.cache = {}
        self.cache_expiry = {}
        self.default_cache_ttl = 300  # 5 minutes

    @staticmethod
    def _cache_result(ttl=None):
        """
        Decorator to cache method results.

        Args:
            ttl: Time to live in seconds (None = default)
        """

        def decorator(func):
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                # Create a cache key from the method name and arguments
                key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

                # Check if we have a cached result that's not expired
                if key in self.cache:
                    expiry = self.cache_expiry.get(key)
                    if expiry and datetime.now() < expiry:
                        logger.debug(f"Cache hit for {key}")
                        return self.cache[key]

                # Call the original function
                result = func(self, *args, **kwargs)

                # Cache the result
                self.cache[key] = result
                cache_ttl = ttl or self.default_cache_ttl
                self.cache_expiry[key] = datetime.now() + timedelta(seconds=cache_ttl)

                return result

            return wrapper

        return decorator

    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()
        self.cache_expiry.clear()
        logger.info("WITSML client cache cleared")

    @_cache_result(ttl=3600)  # Cache for 1 hour
    def get_version(self) -> str:
        """
        Get the WITSML server version.

        Returns:
            WITSML server version string
        """
        return self.connector.get_version()

    @_cache_result(ttl=3600)  # Cache for 1 hour
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get the WITSML server capabilities.

        Returns:
            Dictionary of server capabilities
        """
        cap_xml = self.connector.get_cap()
        return self.parser.parse_xml(cap_xml)

    @_cache_result(ttl=600)  # Cache for 10 minutes
    def get_wells(self) -> List[Dict[str, Any]]:
        """
        Get all wells from the WITSML server.

        Returns:
            List of well information dictionaries
        """
        # Create a simple query that requests all wells
        query_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <wells xmlns="http://www.witsml.org/schemas/1series" version="{self.connector.version}">
            <well/>
        </wells>
        """

        response = self.connector.get_from_store("well", query_xml)
        parsed = self.parser.parse_xml(response)

        if "wells" in parsed and isinstance(parsed["wells"], list):
            return parsed["wells"]
        elif "well" in parsed:
            # If there's only one well, it might be directly in "well"
            return [parsed["well"]]
        return []

    @_cache_result(ttl=600)  # Cache for 10 minutes
    def get_wellbores(self, well_uid: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get wellbores, optionally filtered by well.

        Args:
            well_uid: Optional well UID to filter by

        Returns:
            List of wellbore information dictionaries
        """
        # Build the query based on whether a well_uid is provided
        if well_uid:
            query_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
            <wellbores xmlns="http://www.witsml.org/schemas/1series" version="{self.connector.version}">
                <wellbore uidWell="{well_uid}"/>
            </wellbores>
            """
        else:
            query_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
            <wellbores xmlns="http://www.witsml.org/schemas/1series" version="{self.connector.version}">
                <wellbore/>
            </wellbores>
            """

        response = self.connector.get_from_store("wellbore", query_xml)
        parsed = self.parser.parse_xml(response)

        if "wellbores" in parsed and isinstance(parsed["wellbores"], list):
            return parsed["wellbores"]
        elif "wellbore" in parsed:
            # If there's only one wellbore, it might be directly in "wellbore"
            return [parsed["wellbore"]]
        return []

    @_cache_result(ttl=300)  # Cache for 5 minutes
    def get_logs(self, well_uid: str, wellbore_uid: str) -> List[Dict[str, Any]]:
        """
        Get logs for a specific wellbore.

        Args:
            well_uid: Well UID
            wellbore_uid: Wellbore UID

        Returns:
            List of log information dictionaries
        """
        query_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <logs xmlns="http://www.witsml.org/schemas/1series" version="{self.connector.version}">
            <log uidWell="{well_uid}" uidWellbore="{wellbore_uid}"/>
        </logs>
        """

        response = self.connector.get_from_store("log", query_xml)
        parsed = self.parser.parse_xml(response)

        if "logs" in parsed and isinstance(parsed["logs"], list):
            return parsed["logs"]
        elif "log" in parsed:
            # If there's only one log, it might be directly in "log"
            return [parsed["log"]]
        return []

    @_cache_result(ttl=300)  # Cache for 5 minutes
    def get_log_data(
        self,
        well_uid: str,
        wellbore_uid: str,
        log_uid: str,
        start_index: Optional[str] = None,
        end_index: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get log data for a specific log.

        Args:
            well_uid: Well UID
            wellbore_uid: Wellbore UID
            log_uid: Log UID
            start_index: Optional start index
            end_index: Optional end index

        Returns:
            Dictionary with log data
        """
        # Build indexRange element if start and end are provided
        index_range = ""
        if start_index and end_index:
            index_range = f"""
            <indexRange>
                <startIndex>{start_index}</startIndex>
                <endIndex>{end_index}</endIndex>
            </indexRange>
            """

        query_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <logs xmlns="http://www.witsml.org/schemas/1series" version="{self.connector.version}">
            <log uidWell="{well_uid}" uidWellbore="{wellbore_uid}" uid="{log_uid}">
                {index_range}
            </log>
        </logs>
        """

        response = self.connector.get_from_store("log", query_xml)
        return self.parser.parse_xml(response)

    def check_connection(self) -> bool:
        """
        Check if the connection to the WITSML server is working.

        Returns:
            True if connection is working, False otherwise
        """
        return self.connector.check_connection()
