"""Application and automation catalog endpoints."""

from __future__ import annotations

from flask import Blueprint, Response, jsonify, request

from api.middleware import json_body
from api.serializers import serialize_application, serialize_test_definition
from services.catalog_service import CatalogService
from utils.validators import (
    optional_string,
    parse_bool,
    parse_int,
    require_hex_color,
    require_string,
    require_uuid,
    validate_application_body,
    validate_definition_body,
)

catalog_bp = Blueprint("catalog", __name__)


def _service() -> CatalogService:
    """Build a catalog service for this request.

    Returns:
        A service instance with real repositories.
    """
    return CatalogService()


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
@catalog_bp.get("/applications")
def list_applications() -> Response:
    """List applications in display order.

    Query parameters:
        includeInactive: Whether to include deactivated applications.

    Returns:
        HTTP 200 with an array of serialised applications.
    """
    include_inactive = parse_bool(request.args.get("includeInactive"))
    applications = _service().list_applications(include_inactive=include_inactive)
    return jsonify([serialize_application(app) for app in applications])


@catalog_bp.get("/applications/<application_id>")
def get_application(application_id: str) -> Response:
    """Load one application.

    Args:
        application_id: Path parameter identifying the application.

    Returns:
        HTTP 200 with the serialised application.

    Raises:
        ValidationError: If the identifier is not a UUID.
        NotFoundError: If no such application exists.
    """
    application = _service().get_application(require_uuid(application_id, "applicationId"))
    return jsonify(serialize_application(application))


@catalog_bp.post("/applications")
def create_application() -> tuple[Response, int]:
    """Create an application, or update the one with the same slug.

    Returns:
        HTTP 201 with the serialised application.

    Raises:
        ValidationError: If the payload is malformed.
    """
    payload = validate_application_body(json_body())
    application = _service().create_application(**payload)
    return jsonify(serialize_application(application)), 201


@catalog_bp.put("/applications/<application_id>")
def update_application(application_id: str) -> Response:
    """Update an application's mutable fields.

    Only fields present in the body are changed.

    Args:
        application_id: Path parameter identifying the application.

    Returns:
        HTTP 200 with the updated application.

    Raises:
        ValidationError: If the identifier or payload is malformed.
        NotFoundError: If no such application exists.
    """
    body = json_body()
    application = _service().update_application(
        require_uuid(application_id, "applicationId"),
        name=optional_string(body.get("name"), "name", max_length=120),
        color=require_hex_color(body["color"]) if "color" in body else None,
        display_order=(
            parse_int(body.get("displayOrder"), "displayOrder", default=0, minimum=0, maximum=999)
            if "displayOrder" in body
            else None
        ),
        is_active=parse_bool(body.get("isActive"), default=True) if "isActive" in body else None,
    )
    return jsonify(serialize_application(application))


@catalog_bp.delete("/applications/<application_id>")
def delete_application(application_id: str) -> tuple[str, int]:
    """Hide an application from the interface.

    A soft delete, because run history references it.

    Args:
        application_id: Path parameter identifying the application.

    Returns:
        HTTP 204 with an empty body.

    Raises:
        ValidationError: If the identifier is malformed.
        NotFoundError: If no such application exists.
    """
    _service().deactivate_application(require_uuid(application_id, "applicationId"))
    return "", 204


# ---------------------------------------------------------------------------
# Automations
# ---------------------------------------------------------------------------
@catalog_bp.get("/test-definitions")
def list_test_definitions() -> Response:
    """List active automations for a scope.

    Query parameters:
        scope: Absent selects application-scoped automations, ``general``
            selects general automation, any other value selects that application
            by name.

    Returns:
        HTTP 200 with an array of serialised definitions, main tests first.
    """
    scope = optional_string(request.args.get("scope"), "scope", max_length=120)
    definitions = _service().list_test_definitions(scope)
    return jsonify([serialize_test_definition(entry) for entry in definitions])


@catalog_bp.get("/test-definitions/<definition_id>")
def get_test_definition(definition_id: str) -> Response:
    """Load one automation.

    Args:
        definition_id: Path parameter identifying the definition.

    Returns:
        HTTP 200 with the serialised definition.

    Raises:
        ValidationError: If the identifier is not a UUID.
        NotFoundError: If it does not exist or has been archived.
    """
    definition = _service().get_test_definition(require_uuid(definition_id, "definitionId"))
    return jsonify(serialize_test_definition(definition))


@catalog_bp.get("/test-definitions/by-target")
def get_definition_by_target() -> Response:
    """Resolve an automation by its pytest node id.

    Query parameters:
        target: The node id, such as ``tests/test_login.py::test_valid_login``.

    This is how the automation suite checks whether a test it is about to run is
    registered, without knowing any database identifier.

    Returns:
        HTTP 200 with the serialised definition.

    Raises:
        ValidationError: If ``target`` is absent.
        NotFoundError: If the automation is not registered.
    """
    target = require_string(request.args.get("target"), "target", max_length=300)
    return jsonify(serialize_test_definition(_service().find_by_runner_target(target)))


@catalog_bp.post("/test-definitions")
def register_test_definition() -> tuple[Response, int]:
    """Register an automation, or update the one with the same node id.

    Upsert rather than plain create, so the automation suite can re-register its
    whole catalog on every run without accumulating duplicates.

    Returns:
        HTTP 201 with the serialised definition.

    Raises:
        ValidationError: If the payload is malformed.
        ConflictError: If scope and application disagree, or the application
            already has an active main test.
    """
    payload = validate_definition_body(json_body())
    definition = _service().register_test_definition(**payload)
    return jsonify(serialize_test_definition(definition)), 201


@catalog_bp.delete("/test-definitions/<definition_id>")
def archive_test_definition(definition_id: str) -> tuple[str, int]:
    """Archive an automation so it can no longer be triggered.

    A soft delete, so historic runs remain readable.

    Args:
        definition_id: Path parameter identifying the definition.

    Returns:
        HTTP 204 with an empty body.

    Raises:
        ValidationError: If the identifier is malformed.
        NotFoundError: If it does not exist or was already archived.
    """
    _service().archive_test_definition(require_uuid(definition_id, "definitionId"))
    return "", 204
