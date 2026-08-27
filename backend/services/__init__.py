"""Services: business rules.

No module here imports Flask. Services take plain arguments, raise the
exceptions in :mod:`utils.errors`, and return domain models, which is what makes
them testable without an HTTP client.

Repositories are injected through each constructor so a test can substitute a
fake, and default to a real instance so production code needs no wiring.
"""

from services.analytics_service import AnalyticsService
from services.catalog_service import CatalogService
from services.run_service import RunService

__all__ = ["AnalyticsService", "CatalogService", "RunService"]
