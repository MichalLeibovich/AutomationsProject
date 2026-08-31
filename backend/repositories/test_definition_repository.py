"""Automation catalog persistence."""

from __future__ import annotations

from uuid import UUID

from database import queries
from database.models import TestDefinition
from repositories.base_repository import BaseRepository


class TestDefinitionRepository(BaseRepository):
    """Reads and writes the catalog of runnable automations."""

    def list_by_scope(self, scope: str | None) -> list[TestDefinition]:
        """List active definitions for a scope.

        Args:
            scope: Mirrors the interface selection. None selects
                application-scoped definitions, ``"general"`` selects general
                automation, any other value selects that application by name.

        Returns:
            Definitions with main tests ordered ahead of secondary ones.
        """
        rows = self.fetch_all(queries.SELECT_TEST_DEFINITIONS, {"scope": scope})
        return self.map_all(rows, TestDefinition.from_row)

    def find_by_id(self, definition_id: UUID) -> TestDefinition | None:
        """Load one definition by primary key.

        Args:
            definition_id: The definition's identifier.

        Returns:
            The definition with its application name joined, or None.
        """
        row = self.fetch_one(
            queries.SELECT_TEST_DEFINITION_BY_ID, {"definition_id": str(definition_id)}
        )
        return self.map_one(row, TestDefinition.from_row)

    def find_by_runner_target(self, runner_target: str) -> TestDefinition | None:
        """Load a definition by its pytest node id.

        This is how a runner resolves the automation it just executed back to a
        catalog row without needing to know any database identifier.

        Args:
            runner_target: The node id, such as
                ``tests/test_login.py::test_valid_login``.

        Returns:
            The definition, or None if the automation is not registered.
        """
        row = self.fetch_one(
            queries.SELECT_DEFINITION_BY_TARGET, {"runner_target": runner_target}
        )
        return self.map_one(row, TestDefinition.from_row)

    def find_main_for_application(self, application_id: UUID) -> TestDefinition | None:
        """Load the current active main test of one application.

        Used by the scheduler at tick time so a schedule always fires
        whatever automation is *currently* the application's main test —
        surviving that test being renamed, which archives the old definition
        row and creates a new one.

        Args:
            application_id: The owning application.

        Returns:
            The main definition, or None if the application has none active.
        """
        row = self.fetch_one(
            queries.SELECT_MAIN_DEFINITION_FOR_APPLICATION,
            {"application_id": str(application_id)},
        )
        return self.map_one(row, TestDefinition.from_row)

    def list_main_for_bulk(self, scope: str | None) -> list[TestDefinition]:
        """List the main test of every active application in scope.

        General automation is excluded by the query itself rather than by the
        caller, so no code path can bulk-trigger it.

        Args:
            scope: Application name to restrict to, or None for all.

        Returns:
            One main definition per matching application, in display order.
        """
        rows = self.fetch_all(queries.SELECT_MAIN_DEFINITIONS_FOR_BULK, {"scope": scope})
        return self.map_all(rows, TestDefinition.from_row)

    def upsert(
        self,
        *,
        application_id: UUID | None,
        scope: str,
        kind: str,
        name: str,
        runner_target: str,
        description: str | None = None,
        display_order: int = 0,
        timeout_seconds: int = 600,
    ) -> TestDefinition:
        """Register an automation, or update the existing one with the same node id.

        Upsert rather than plain insert, so re-registering the catalog from the
        automation suite is idempotent.

        Args:
            application_id: Owning application, or None for general automation.
            scope: ``"application"`` or ``"general"``.
            kind: ``"main"``, ``"secondary"`` or ``"general"``.
            name: Display name.
            runner_target: pytest node id the runner executes.
            description: Optional longer description.
            display_order: Sort position within its card.
            timeout_seconds: Runner timeout.

        Returns:
            The created or updated definition.

        Raises:
            psycopg2.Error: If scope and application disagree, which the database
                rejects via a check constraint.
        """
        row = self.execute_returning(
            queries.INSERT_TEST_DEFINITION,
            {
                "application_id": str(application_id) if application_id else None,
                "scope": scope,
                "kind": kind,
                "name": name,
                "description": description,
                "runner_target": runner_target,
                "display_order": display_order,
                "timeout_seconds": timeout_seconds,
            },
        )
        assert row is not None, "INSERT_TEST_DEFINITION always returns a row"
        return TestDefinition.from_row(row)

    def archive(self, definition_id: UUID) -> bool:
        """Archive a definition so it can no longer be triggered.

        A soft delete, so historic runs remain readable.

        Args:
            definition_id: The definition to archive.

        Returns:
            True if a row was updated.
        """
        return (
            self.execute(queries.ARCHIVE_TEST_DEFINITION, {"definition_id": str(definition_id)})
            > 0
        )
