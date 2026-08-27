"""Application and automation catalog management."""

from __future__ import annotations

from uuid import UUID

from database.models import Application, TestDefinition
from repositories.application_repository import ApplicationRepository
from repositories.test_definition_repository import TestDefinitionRepository
from utils.errors import ConflictError, NotFoundError
from utils.logger import get_logger

logger = get_logger(__name__)


class CatalogService:
    """Manages the catalog of applications and runnable automations."""

    def __init__(
        self,
        application_repository: ApplicationRepository | None = None,
        definition_repository: TestDefinitionRepository | None = None,
    ) -> None:
        """Initialise the service.

        Args:
            application_repository: Application persistence. Defaults to a real
                repository.
            definition_repository: Definition persistence. Defaults to a real
                repository.
        """
        self._applications = application_repository or ApplicationRepository()
        self._definitions = definition_repository or TestDefinitionRepository()

    # -- applications -------------------------------------------------------
    def list_applications(self, *, include_inactive: bool = False) -> list[Application]:
        """List applications in display order.

        Args:
            include_inactive: Whether to include deactivated applications.

        Returns:
            The matching applications.
        """
        return self._applications.list_all(include_inactive=include_inactive)

    def get_application(self, application_id: UUID) -> Application:
        """Load one application.

        Args:
            application_id: The application to load.

        Returns:
            The application.

        Raises:
            NotFoundError: If no such application exists.
        """
        application = self._applications.find_by_id(application_id)
        if application is None:
            raise NotFoundError("האפליקציה לא נמצאה")
        return application

    def create_application(
        self, *, name: str, slug: str, color: str, display_order: int = 0
    ) -> Application:
        """Create an application, or update the one with the same slug.

        Args:
            name: Display name.
            slug: Stable identifier, used as the conflict target.
            color: Identity colour as ``#RRGGBB``.
            display_order: Sort position.

        Returns:
            The created or updated application.
        """
        return self._applications.upsert(
            name=name, slug=slug, color=color, display_order=display_order
        )

    def update_application(
        self,
        application_id: UUID,
        *,
        name: str | None = None,
        color: str | None = None,
        display_order: int | None = None,
        is_active: bool | None = None,
    ) -> Application:
        """Update an application's mutable fields.

        Args:
            application_id: The application to update.
            name: New display name, or None to leave unchanged.
            color: New identity colour, or None.
            display_order: New sort position, or None.
            is_active: New active flag, or None.

        Returns:
            The updated application.

        Raises:
            NotFoundError: If no such application exists.
        """
        updated = self._applications.update(
            application_id,
            name=name,
            color=color,
            display_order=display_order,
            is_active=is_active,
        )
        if updated is None:
            raise NotFoundError("האפליקציה לא נמצאה")
        return updated

    def deactivate_application(self, application_id: UUID) -> None:
        """Hide an application from the interface.

        A soft delete. Run history stores a frozen scope label, so past runs stay
        readable while the application leaves the filter row.

        Args:
            application_id: The application to deactivate.

        Raises:
            NotFoundError: If no such application exists.
        """
        if not self._applications.deactivate(application_id):
            raise NotFoundError("האפליקציה לא נמצאה")

    # -- automations --------------------------------------------------------
    def list_test_definitions(self, scope: str | None) -> list[TestDefinition]:
        """List active automations for a scope.

        Args:
            scope: None for application-scoped automations, ``"general"`` for
                general automation, or an application name.

        Returns:
            The matching definitions, main tests first.
        """
        return self._definitions.list_by_scope(scope)

    def get_test_definition(self, definition_id: UUID) -> TestDefinition:
        """Load one automation.

        Args:
            definition_id: The definition to load.

        Returns:
            The definition.

        Raises:
            NotFoundError: If it does not exist or has been archived.
        """
        definition = self._definitions.find_by_id(definition_id)
        if definition is None:
            raise NotFoundError("הבדיקה לא נמצאה")
        return definition

    def find_by_runner_target(self, runner_target: str) -> TestDefinition:
        """Resolve an automation by its pytest node id.

        This is the lookup a runner uses to attach results to the right catalog
        row without knowing any database identifier.

        Args:
            runner_target: The node id, such as
                ``tests/test_login.py::test_valid_login``.

        Returns:
            The definition.

        Raises:
            NotFoundError: If the automation is not registered. Registering it
                first is deliberate: an unregistered test writing results would
                create catalog entries nobody chose.
        """
        definition = self._definitions.find_by_runner_target(runner_target)
        if definition is None:
            raise NotFoundError(f"האוטומציה '{runner_target}' אינה רשומה במערכת")
        return definition

    def register_test_definition(
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
        """Register an automation, or update the one with the same node id.

        Scope consistency is checked here as well as by a database constraint, so
        a misconfigured request produces a clear message rather than a constraint
        violation.

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
            The registered definition.

        Raises:
            ConflictError: If scope and application do not agree, or the
                application already has an active main test.
        """
        if scope == "application" and application_id is None:
            raise ConflictError("בדיקה בתחום אפליקציה חייבת להיות משויכת לאפליקציה")
        if scope == "general" and application_id is not None:
            raise ConflictError("אוטומציה כללית אינה משויכת לאפליקציה")

        try:
            registered = self._definitions.upsert(
                application_id=application_id,
                scope=scope,
                kind=kind,
                name=name,
                runner_target=runner_target,
                description=description,
                display_order=display_order,
                timeout_seconds=timeout_seconds,
            )
        except Exception as exc:
            # The partial unique index permits one active main test per
            # application; a second is a configuration mistake, not a fault.
            if "test_definitions_one_main_per_app" in str(exc):
                raise ConflictError("לאפליקציה כבר מוגדרת בדיקה ראשית פעילה") from exc
            raise

        logger.info("automation registered", extra={"target": runner_target, "kind": kind})
        return registered

    def archive_test_definition(self, definition_id: UUID) -> None:
        """Archive an automation so it can no longer be triggered.

        Args:
            definition_id: The definition to archive.

        Raises:
            NotFoundError: If it does not exist or was already archived.
        """
        if not self._definitions.archive(definition_id):
            raise NotFoundError("הבדיקה לא נמצאה")
