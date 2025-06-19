"""
FastAPI middleware components.
"""

from src.api.middlewares.metrics import MetricsMiddleware

__all__ = ["MetricsMiddleware"]
