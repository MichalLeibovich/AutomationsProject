"""Run artifact and comment persistence."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from database import queries
from database.connection import transaction
from database.models import RunArtifact, RunComment
from repositories.base_repository import BaseRepository
from utils.logger import get_logger

logger = get_logger(__name__)


class ArtifactRepository(BaseRepository):
    """Reads and writes artifact metadata.

    Only metadata is stored relationally. Screenshots and traces live on disk or
    in object storage, because holding binaries in PostgreSQL would bloat every
    backup and make partition drops expensive.
    """

    def list_by_run(self, run_id: UUID) -> list[RunArtifact]:
        """List every artifact belonging to a run.

        Args:
            run_id: The run whose artifacts to read.

        Returns:
            Artifacts ordered by kind, then file name.
        """
        rows = self.fetch_all(queries.SELECT_ARTIFACTS_BY_RUN, {"run_id": str(run_id)})
        return self.map_all(rows, RunArtifact.from_row)

    def create(
        self,
        *,
        run_id: UUID,
        run_started_at: datetime,
        kind: str,
        file_name: str,
        local_path: str | None = None,
        s3_bucket: str | None = None,
        s3_key: str | None = None,
        content_type: str = "application/octet-stream",
        size_bytes: int = 0,
    ) -> RunArtifact:
        """Record metadata for a file a runner produced.

        Either a local path or an object key must be supplied; the database
        enforces that, because an artifact nobody can locate is not an artifact.

        Args:
            run_id: The run that produced the file.
            run_started_at: The run's start time, for the composite foreign key.
            kind: screenshot, log, trace, video, har or report.
            file_name: Original file name.
            local_path: Path on a shared filesystem, when used.
            s3_bucket: Bucket holding the object, when used.
            s3_key: Object key, when used.
            content_type: MIME type.
            size_bytes: File size.

        Returns:
            The created artifact record.

        Raises:
            psycopg2.Error: If the insert fails.
        """
        with transaction() as cursor:
            cursor.execute(
                queries.INSERT_ARTIFACT,
                {
                    "run_id": str(run_id),
                    "run_started_at": run_started_at,
                    "kind": kind,
                    "file_name": file_name,
                    "local_path": local_path,
                    "s3_bucket": s3_bucket,
                    "s3_key": s3_key,
                    "content_type": content_type,
                    "size_bytes": size_bytes,
                },
            )
            row = cursor.fetchone()
            cursor.execute(queries.UPDATE_RUN_ARTIFACT_COUNT, {"run_id": str(run_id)})

        assert row is not None, "INSERT_ARTIFACT always returns a row"
        return RunArtifact.from_row(dict(row))


class CommentRepository(BaseRepository):
    """Reads and writes free-text operator notes attached to runs."""

    def list_by_run(self, run_id: UUID) -> list[RunComment]:
        """List a run's comments in chronological order.

        Soft-deleted comments are excluded.

        Args:
            run_id: The run whose comments to read.

        Returns:
            The comments, oldest first.
        """
        rows = self.fetch_all(queries.SELECT_COMMENTS_BY_RUN, {"run_id": str(run_id)})
        return self.map_all(rows, RunComment.from_row)

    def create(
        self, *, run_id: UUID, run_started_at: datetime, author_name: str, body: str
    ) -> RunComment:
        """Add a comment to a run.

        Args:
            run_id: The run being commented on.
            run_started_at: The run's start time, for the composite foreign key.
            author_name: Free-text author name; there are no accounts.
            body: Comment text, already validated.

        Returns:
            The created comment.

        Raises:
            psycopg2.Error: If the insert fails.
        """
        row = self.execute_returning(
            queries.INSERT_COMMENT,
            {
                "run_id": str(run_id),
                "run_started_at": run_started_at,
                "author_name": author_name,
                "body": body,
            },
        )
        assert row is not None, "INSERT_COMMENT always returns a row"
        logger.info("comment added", extra={"run_id": str(run_id)})
        return RunComment.from_row(row)

    def soft_delete(self, comment_id: UUID) -> bool:
        """Mark a comment deleted, retaining the row.

        Args:
            comment_id: The comment to remove.

        Returns:
            True if a row was updated.
        """
        return self.execute(queries.SOFT_DELETE_COMMENT, {"comment_id": str(comment_id)}) > 0
