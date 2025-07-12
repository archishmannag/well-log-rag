import logging
import time
from typing import Optional
from zeep import Client
from zeep.exceptions import TransportError
from zeep.wsse.username import UsernameToken
from zeep.cache import SqliteCache
from zeep.transports import Transport
from requests.exceptions import Timeout, ConnectionError

from src.api.config import settings

logger = logging.getLogger(__name__)


class WitsmlConnector:
    """
    Connector for WITSML servers using SOAP protocol.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        version: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """
        Initialize the WITSML connector.

        Args:
            url: WITSML server URL (defaults to config)
            username: WITSML server username (defaults to config)
            password: WITSML server password (defaults to config)
            version: WITSML version (defaults to config)
            timeout: Connection timeout in seconds (defaults to config)
        """
        self.url = url or settings.WITSML_SERVER_URL
        self.username = username or settings.WITSML_USERNAME
        self.password = password or settings.WITSML_PASSWORD
        self.version = version or settings.WITSML_VERSION
        self.timeout = timeout or settings.WITSML_TIMEOUT

        if not self.url:
            raise ValueError("WITSML server URL is required")

        # Initialize the SOAP client
        self._initialize_client()

        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    def _initialize_client(self):
        """Initialize the SOAP client with proper configuration."""
        try:
            # Setup caching
            cache = SqliteCache(path="/tmp/zeep-cache.db")

            # Setup transport with timeout and cache
            transport = Transport(
                cache=cache,
                timeout=self.timeout,
                operation_timeout=self.timeout,
            )

            # Initialize client with security if credentials are provided
            if self.username and self.password:
                self.client = Client(
                    self.url,
                    transport=transport,
                    wsse=UsernameToken(self.username, self.password),
                )
            else:
                self.client = Client(self.url, transport=transport)

            logger.info(f"WITSML SOAP client initialized for {self.url}")
        except Exception as e:
            logger.error(f"Failed to initialize WITSML SOAP client: {str(e)}")
            raise

    def execute_with_retry(self, operation, *args, **kwargs):
        """
        Execute a SOAP operation with retry logic.

        Args:
            operation: The operation function to call
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            Operation result
        """
        retries = 0
        last_exception = None

        while retries < self.max_retries:
            try:
                return operation(*args, **kwargs)
            except (TransportError, Timeout, ConnectionError) as e:
                # These are retryable errors
                retries += 1
                last_exception = e

                if retries < self.max_retries:
                    wait_time = self.retry_delay * (
                        2 ** (retries - 1)
                    )  # Exponential backoff
                    logger.warning(
                        f"WITSML operation failed, retrying in {wait_time} seconds. "
                        f"Error: {str(e)}, Attempt: {retries}/{self.max_retries}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"WITSML operation failed after {self.max_retries} attempts. "
                        f"Error: {str(e)}"
                    )
            except Exception as e:
                # Non-retryable errors
                logger.error(
                    f"WITSML operation failed with non-retryable error: {str(e)}"
                )
                raise

        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        raise RuntimeError("WITSML operation failed with unknown error")

    def get_version(self) -> str:
        """
        Get the WITSML server version.

        Returns:
            WITSML server version string
        """
        try:
            result = self.execute_with_retry(self.client.service.WMLS_GetVersion)
            return result
        except Exception as e:
            logger.error(f"Failed to get WITSML version: {str(e)}")
            raise

    def get_cap(self) -> str:
        """
        Get the WITSML server capabilities.

        Returns:
            WITSML server capabilities as XML string
        """
        try:
            result = self.execute_with_retry(self.client.service.WMLS_GetCap)
            return result
        except Exception as e:
            logger.error(f"Failed to get WITSML capabilities: {str(e)}")
            raise

    def get_base_msg(self) -> str:
        """
        Get the server base message.

        Returns:
            Server base message
        """
        try:
            result = self.execute_with_retry(self.client.service.WMLS_GetBaseMsg)
            return result
        except Exception as e:
            logger.error(f"Failed to get WITSML base message: {str(e)}")
            raise

    def get_from_store(
        self, object_type: str, query_xml: str, options: Optional[str] = None
    ) -> str:
        """
        Retrieve data from the WITSML store.

        Args:
            object_type: WITSML object type (e.g., "well", "wellbore", "log")
            query_xml: WITSML query in XML format
            options: Query options

        Returns:
            WITSML data as XML string
        """
        try:
            options = options or "returnElements=all"

            result = self.execute_with_retry(
                self.client.service.WMLS_GetFromStore,
                object_type,
                query_xml,
                options,
            )

            # The result is a tuple of (returnCode, XMLout)
            return_code, xml_out = result

            if return_code != 1:  # 1 is success in WITSML
                error_msg = self.get_error_message(return_code)
                raise Exception(
                    f"WITSML GetFromStore failed: {error_msg} (code: {return_code})"
                )

            return xml_out
        except Exception as e:
            logger.error(f"Failed to get data from WITSML store: {str(e)}")
            raise

    def add_to_store(
        self, object_type: str, xml_in: str, options: Optional[str] = None
    ) -> int:
        """
        Add data to the WITSML store.

        Args:
            object_type: WITSML object type
            xml_in: XML data to add
            options: Options string

        Returns:
            Return code (1 = success)
        """
        try:
            options = options or ""

            return_code = self.execute_with_retry(
                self.client.service.WMLS_AddToStore,
                object_type,
                xml_in,
                options,
            )

            if return_code != 1:
                error_msg = self.get_error_message(return_code)
                raise Exception(
                    f"WITSML AddToStore failed: {error_msg} (code: {return_code})"
                )

            return return_code
        except Exception as e:
            logger.error(f"Failed to add data to WITSML store: {str(e)}")
            raise

    def update_in_store(
        self, object_type: str, xml_in: str, options: Optional[str] = None
    ) -> int:
        """
        Update data in the WITSML store.

        Args:
            object_type: WITSML object type
            xml_in: XML data to update
            options: Options string

        Returns:
            Return code (1 = success)
        """
        try:
            options = options or ""

            return_code = self.execute_with_retry(
                self.client.service.WMLS_UpdateInStore,
                object_type,
                xml_in,
                options,
            )

            if return_code != 1:
                error_msg = self.get_error_message(return_code)
                raise Exception(
                    f"WITSML UpdateInStore failed: {error_msg} (code: {return_code})"
                )

            return return_code
        except Exception as e:
            logger.error(f"Failed to update data in WITSML store: {str(e)}")
            raise

    def delete_from_store(
        self, object_type: str, xml_in: str, options: Optional[str] = None
    ) -> int:
        """
        Delete data from the WITSML store.

        Args:
            object_type: WITSML object type
            xml_in: XML query specifying what to delete
            options: Options string

        Returns:
            Return code (1 = success)
        """
        try:
            options = options or ""

            return_code = self.execute_with_retry(
                self.client.service.WMLS_DeleteFromStore,
                object_type,
                xml_in,
                options,
            )

            if return_code != 1:
                error_msg = self.get_error_message(return_code)
                raise Exception(
                    f"WITSML DeleteFromStore failed: {error_msg} (code: {return_code})"
                )

            return return_code
        except Exception as e:
            logger.error(f"Failed to delete data from WITSML store: {str(e)}")
            raise

    def get_error_message(self, error_code: int) -> str:
        """
        Get the error message for a WITSML error code.

        Args:
            error_code: WITSML error code

        Returns:
            Error message
        """
        try:
            return self.execute_with_retry(
                self.client.service.WMLS_GetBaseMsg, error_code
            )
        except Exception:
            # If we can't get the error message, return a generic one
            return f"Unknown error (code: {error_code})"

    def check_connection(self) -> bool:
        """
        Check if the connection to the WITSML server is working.

        Returns:
            True if connection is working, False otherwise
        """
        try:
            self.get_version()
            return True
        except Exception:
            return False

    def connect(self):
        """
        Explicitly connect to the WITSML server.

        This method re-initializes the SOAP client if needed and verifies
        the connection by attempting to get the server version.

        Raises:
            Exception: If connection fails
        """
        try:
            # Check if client needs initialization
            if not hasattr(self, "client") or self.client is None:
                self._initialize_client()

            # Verify connection by getting version
            version = self.get_version()
            logger.info(
                f"Successfully connected to WITSML server at {self.url} (version: {version})"
            )
        except Exception as e:
            logger.error(f"Failed to connect to WITSML server: {str(e)}")
            raise

    def disconnect(self):
        """
        Disconnect from the WITSML server.

        Closes any open connections and performs cleanup.
        """
        try:
            # In zeep, we need to close the underlying transport session
            if hasattr(self, "client") and self.client is not None:
                if hasattr(self.client.transport, "session"):
                    self.client.transport.session.close()
                    logger.info(f"Disconnected from WITSML server at {self.url}")
        except Exception as e:
            logger.warning(f"Error during WITSML server disconnect: {str(e)}")

        # Set client to None to ensure it's recreated on next use
        self.client = None

    def __enter__(self):
        """
        Context manager entry point.
        """
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point.
        """
        self.disconnect()
