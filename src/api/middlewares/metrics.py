import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

from src.api.config import settings

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting and reporting API usage metrics.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.app = app
        # Initialize metrics storage
        self.request_counts = {}
        self.response_times = {}
        # Set log level from configuration
        logger.setLevel(settings.LOG_LEVEL)

    async def dispatch(self, request: Request, call_next):
        # Record request start time
        start_time = time.time()

        # Get path for grouping metrics
        path = request.url.path
        method = request.method

        # Update request count
        key = f"{method}:{path}"
        self.request_counts[key] = self.request_counts.get(key, 0) + 1

        # Process the request
        try:
            response = await call_next(request)

            # Record response time
            process_time = time.time() - start_time
            if key not in self.response_times:
                self.response_times[key] = []
            self.response_times[key].append(process_time)

            # Log metrics with configurable level
            if process_time > 1.0:  # Slow request
                logger.warning(
                    f"Slow request: {key} | Status: {response.status_code} | Time: {process_time:.4f}s"
                )
            else:
                logger.info(
                    f"Request: {key} | Status: {response.status_code} | Time: {process_time:.4f}s"
                )

            return response
        except Exception as e:
            # Log errors
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {key} | Error: {str(e)} | Time: {process_time:.4f}s"
            )
            raise
