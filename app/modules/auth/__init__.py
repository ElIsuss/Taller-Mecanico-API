"""Compatibility layer: re-exporting from app.modules.usuarios."""

from app.modules.usuarios import models, router, schemas, service

__all__ = ["models", "router", "schemas", "service"]

