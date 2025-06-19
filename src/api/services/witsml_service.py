import logging
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import threading

from src.witsml.client import WitsmlClient
from src.witsml.processor import WitsmlProcessor
from src.api.config import settings

logger = logging.getLogger(__name__)


class WitsmlService:
    """
    Service layer for WITSML operations.
    """

    def __init__(self):
        """Initialize the WITSML service."""
        # Client pool management
        self.client_pool = []
        self.client_pool_lock = threading.Lock()
        self.max_pool_size = 5
        self.processor = WitsmlProcessor()

        # Create initial client
        self._ensure_client_pool()

    def _ensure_client_pool(self):
        """Ensure the client pool has at least one client."""
        with self.client_pool_lock:
            if not self.client_pool:
                # Create a new client and add to pool
                client = WitsmlClient(
                    url=settings.WITSML_SERVER_URL,
                    username=settings.WITSML_USERNAME,
                    password=settings.WITSML_PASSWORD,
                    version=settings.WITSML_VERSION,
                )
                self.client_pool.append(client)

    def _get_client(self) -> WitsmlClient:
        """
        Get a client from the pool or create a new one if needed.

        Returns:
            WitsmlClient instance
        """
        with self.client_pool_lock:
            if not self.client_pool:
                # Create a new client
                client = WitsmlClient(
                    url=settings.WITSML_SERVER_URL,
                    username=settings.WITSML_USERNAME,
                    password=settings.WITSML_PASSWORD,
                    version=settings.WITSML_VERSION,
                )
                return client

            # Take a client from the pool
            return self.client_pool.pop()

    def _return_client(self, client: WitsmlClient):
        """
        Return a client to the pool.

        Args:
            client: WitsmlClient instance to return
        """
        with self.client_pool_lock:
            if len(self.client_pool) < self.max_pool_size:
                self.client_pool.append(client)
            # If pool is full, the client will be garbage collected

    def get_wells(self) -> List[Dict[str, Any]]:
        """
        Get all wells from the WITSML server.

        Returns:
            List of well information dictionaries
        """
        client = self._get_client()
        try:
            return client.get_wells()
        finally:
            self._return_client(client)

    def get_wellbores(self, well_uid: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get wellbores, optionally filtered by well.

        Args:
            well_uid: Optional well UID to filter by

        Returns:
            List of wellbore information dictionaries
        """
        client = self._get_client()
        try:
            return client.get_wellbores(well_uid)
        finally:
            self._return_client(client)

    def get_logs(self, well_uid: str, wellbore_uid: str) -> List[Dict[str, Any]]:
        """
        Get logs for a specific wellbore.

        Args:
            well_uid: Well UID
            wellbore_uid: Wellbore UID

        Returns:
            List of log information dictionaries
        """
        client = self._get_client()
        try:
            return client.get_logs(well_uid, wellbore_uid)
        finally:
            self._return_client(client)

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
        client = self._get_client()
        try:
            log_data = client.get_log_data(
                well_uid, wellbore_uid, log_uid, start_index, end_index
            )

            # Process the log data
            if "log" in log_data:
                # Convert to XML for processor
                # In a real implementation, we'd need to convert the parsed data back to XML
                # For now we'll assume the processor can work with the parsed data directly
                processed_data = self.processor.process_file(log_data["log"])
                return processed_data
            return log_data
        finally:
            self._return_client(client)

    def check_connection(self) -> bool:
        """
        Check if the connection to the WITSML server is working.

        Returns:
            True if connection is working, False otherwise
        """
        client = self._get_client()
        try:
            return client.check_connection()
        finally:
            self._return_client(client)

    def get_server_info(self) -> Dict[str, Any]:
        """
        Get server information.

        Returns:
            Dictionary with server information
        """
        client = self._get_client()
        try:
            version = client.get_version()
            capabilities = client.get_capabilities()

            return {
                "version": version,
                "capabilities": capabilities,
                "url": settings.WITSML_SERVER_URL,
                "status": "connected" if client.check_connection() else "disconnected",
            }
        finally:
            self._return_client(client)

    def clear_cache(self):
        """Clear cache on all clients in the pool."""
        with self.client_pool_lock:
            for client in self.client_pool:
                client.clear_cache()
            logger.info("Cleared cache on all WITSML clients")

    def get_wells_batch(self, well_uids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get multiple wells in parallel.

        Args:
            well_uids: List of well UIDs

        Returns:
            Dictionary mapping well UIDs to well data
        """
        results = {}

        def fetch_well(uid):
            client = self._get_client()
            try:
                # This is a simplified example - in reality we would need a more specific query
                wells = client.get_wells()
                for well in wells:
                    if well.get("uid") == uid:
                        return uid, well
                return uid, None
            finally:
                self._return_client(client)

        with ThreadPoolExecutor(
            max_workers=min(len(well_uids), self.max_pool_size)
        ) as executor:
            for uid, well_data in executor.map(fetch_well, well_uids):
                if well_data:
                    results[uid] = well_data

        return results
