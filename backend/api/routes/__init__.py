"""Route blueprints, one module per resource.

Each does HTTP only: parse the request, delegate to a service, serialise the
result. Blueprints are registered by :mod:`server`.
"""

from api.routes.analytics_routes import analytics_bp
from api.routes.catalog_routes import catalog_bp
from api.routes.health_routes import health_bp
from api.routes.run_routes import run_bp
from api.routes.schedule_routes import schedule_bp

ALL_BLUEPRINTS = (health_bp, catalog_bp, run_bp, analytics_bp, schedule_bp)
"""Every blueprint, in registration order."""

__all__ = [
    "ALL_BLUEPRINTS",
    "analytics_bp",
    "catalog_bp",
    "health_bp",
    "run_bp",
    "schedule_bp",
]
