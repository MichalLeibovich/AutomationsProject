"""Application catalog persistence."""

from __future__ import annotations

from uuid import UUID

from database import queries
from database.models import Application
from repositories.base_repository import BaseRepository


class ApplicationRepository(BaseRepository):
    """Reads and writes the monitored application catalog."""

    def list_all(self, *, include_inactive: bool = False) -> list[Application]:
        """List applications in display order.

        Args:
            include_inactive: Whether to include deactivated applications, which
                are retained because run history references them.

        Returns:
            Applications ordered by display order, then name.
        """
        rows = self.fetch_all(queries.SELECT_APPLICATIONS, {"include_inactive": include_inactive})
        return self.map_all(rows, Application.from_row)

    def find_by_id(self, application_id: UUID) -> Application | None:
        """Load one application by primary key.

        Args:
            application_id: The application's identifier.

        Returns:
            The application, or None if no such row exists.
        """
        row = self.fetch_one(
            queries.SELECT_APPLICATION_BY_ID, {"application_id": str(application_id)}
        )
        return self.map_one(row, Application.from_row)

    def upsert(self, *, name: str, slug: str, color: str, display_order: int = 0) -> Application:
        """Create an application, or update the existing one with the same slug.

        Args:
            name: Display name.
            slug: Stable identifier, the conflict target.
            color: Identity colour as ``#RRGGBB``.
            display_order: Sort position.

        Returns:
            The created or updated application.

        Raises:
            psycopg2.Error: If the statement fails.
        """
        row = self.execute_returning(
            queries.UPSERT_APPLICATION,
            {"name": name, "slug": slug, "color": color, "display_order": display_order},
        )
        assert row is not None, "UPSERT_APPLICATION always returns a row"
        return Application.from_row(row)

    def update(
        self,
        application_id: UUID,
        *,
        name: str | None = None,
        color: str | None = None,
        display_order: int | None = None,
        is_active: bool | None = None,
    ) -> Application | None:
        """Update an application's mutable fields.

        Arguments left as None are not modified.

        Args:
            application_id: The application to update.
            name: New display name, or None.
            color: New identity colour, or None.
            display_order: New sort position, or None.
            is_active: New active flag, or None.

        Returns:
            The updated application, or None if no such row exists.
        """
        row = self.execute_returning(
            queries.UPDATE_APPLICATION,
            {
                "application_id": str(application_id),
                "name": name,
                "color": color,
                "display_order": display_order,
                "is_active": is_active,
            },
        )
        return self.map_one(row, Application.from_row)

    def deactivate(self, application_id: UUID) -> bool:
        """Hide an application from the interface.

        A soft delete: run history stores a frozen scope label, so past runs stay
        readable while the application leaves the filter row.

        Args:
            application_id: The application to deactivate.

        Returns:
            True if a row was updated.
        """
        return (
            self.execute(
                queries.DEACTIVATE_APPLICATION, {"application_id": str(application_id)}
            )
            > 0
        )
