"""Domain models to JSON.

Kept out of both routes and services: the wire format is a presentation concern,
and centralising it means the camelCase contract cannot drift between endpoints.
"""

from __future__ import annotations

from typing import Any, Callable

from database.models import (
    Application,
    Page,
    RunArtifact,
    RunComment,
    RunStep,
    TestDefinition,
    TestRun,
)
from utils.helpers import iso


def serialize_application(application: Application) -> dict[str, Any]:
    """Serialise an application.

    Args:
        application: The application to serialise.

    Returns:
        A camelCase mapping.
    """
    return {
        "id": str(application.id),
        "name": application.name,
        "slug": application.slug,
        "color": application.color,
        "displayOrder": application.display_order,
        "isActive": application.is_active,
    }


def serialize_test_definition(definition: TestDefinition) -> dict[str, Any]:
    """Serialise an automation definition.

    ``runnerTarget`` is included, unlike most internal fields: the automation
    suite needs it to match its own tests against the catalog.

    Args:
        definition: The definition to serialise.

    Returns:
        A camelCase mapping.
    """
    return {
        "id": str(definition.id),
        "applicationId": (
            str(definition.application_id) if definition.application_id else None
        ),
        "applicationName": definition.application_name,
        "scope": definition.scope,
        "kind": definition.kind,
        "name": definition.name,
        "description": definition.description,
        "runnerTarget": definition.runner_target,
        "displayOrder": definition.display_order,
        "timeoutSeconds": definition.timeout_seconds,
        "isActive": definition.is_active,
    }


def serialize_run(run: TestRun) -> dict[str, Any]:
    """Serialise a run.

    Args:
        run: The run to serialise.

    Returns:
        A camelCase mapping. ``failure`` is None unless the run failed, in which
        case it carries the feature, error type, reason and stack trace.
        Timestamps are ISO 8601 strings.
    """
    return {
        "id": str(run.id),
        "testDefinitionId": str(run.test_definition_id),
        "testName": run.test_name,
        "runnerTarget": run.runner_target,
        "applicationId": str(run.application_id) if run.application_id else None,
        "scope": run.scope,
        "scopeLabel": run.scope_label,
        "status": run.status,
        "queuedAt": iso(run.queued_at),
        "startedAt": iso(run.started_at),
        "endedAt": iso(run.ended_at),
        "durationSeconds": run.duration_seconds,
        "triggeredBy": run.triggered_by,
        "triggerSource": run.trigger_source,
        "workerId": run.worker_id,
        "attempt": run.attempt,
        "totalSteps": run.total_steps,
        "failedSteps": run.failed_steps,
        "artifactCount": run.artifact_count,
        "failure": (
            {
                "feature": run.failure.feature,
                "errorType": run.failure.error_type,
                "reason": run.failure.reason,
                "stackTrace": run.failure.stack_trace,
            }
            if run.failure
            else None
        ),
    }


def serialize_step(step: RunStep) -> dict[str, Any]:
    """Serialise one step of a run.

    Args:
        step: The step to serialise.

    Returns:
        A camelCase mapping.
    """
    return {
        "id": str(step.id),
        "runId": str(step.run_id),
        "index": step.step_index,
        "name": step.name,
        "status": step.status,
        "durationMs": step.duration_ms,
        "errorMessage": step.error_message,
        "startedAt": iso(step.started_at),
    }


def serialize_artifact(artifact: RunArtifact) -> dict[str, Any]:
    """Serialise an artifact.

    Args:
        artifact: The artifact metadata record.

    Returns:
        A camelCase mapping including a download path when the file was written
        locally.
    """
    return {
        "id": str(artifact.id),
        "runId": str(artifact.run_id),
        "kind": artifact.kind,
        "fileName": artifact.file_name,
        "contentType": artifact.content_type,
        "sizeBytes": artifact.size_bytes,
        "downloadUrl": (
            f"/api/runs/{artifact.run_id}/artifacts/{artifact.id}/download"
            if artifact.local_path
            else None
        ),
    }


def serialize_comment(comment: RunComment) -> dict[str, Any]:
    """Serialise a run comment.

    Args:
        comment: The comment to serialise.

    Returns:
        A camelCase mapping.
    """
    return {
        "id": str(comment.id),
        "runId": str(comment.run_id),
        "authorName": comment.author_name,
        "body": comment.body,
        "createdAt": iso(comment.created_at),
    }


def serialize_page(
    page: Page, item_serializer: Callable[[Any], dict[str, Any]]
) -> dict[str, Any]:
    """Serialise a page of results.

    Args:
        page: The page to serialise.
        item_serializer: Serialiser applied to each item.

    Returns:
        A camelCase mapping with ``items``, ``total``, ``limit`` and ``offset``.
    """
    return {
        "items": [item_serializer(item) for item in page.items],
        "total": page.total,
        "limit": page.limit,
        "offset": page.offset,
    }
