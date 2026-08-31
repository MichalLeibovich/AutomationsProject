import { forwardRef, useEffect, useImperativeHandle, useState } from 'react';
import { useAtomValue, useSetAtom } from 'jotai';

import { Avatar, IconButton, TextField, Tooltip } from '@mui/material';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

import WarningIcon from '@mui/icons-material/WarningAmberRounded';
import ImageIcon from '@mui/icons-material/ImageOutlined';
import SendIcon from '@mui/icons-material/SendRounded';

import { Button } from '@/components/Button/Button';
import { IdentityDot } from '@/components/IdentityDot/IdentityDot';
import { StatusBadge } from '@/components/StatusBadge/StatusBadge';

import { applicationsAtom } from '@/atoms/appAtom';
import { pushToastAtom } from '@/atoms/toastAtom';

import { runService } from '@/services/runService';
import { useRunComments } from '@/hooks/useRuns';
import { he } from '@/locales/he';
import type { RunArtifact, TestRun } from '@/types/run.types';
import { formatDuration, formatShortDate, formatTime, initials } from '@/utils/format';
import { resolveScopeColor } from '@/utils/scope';

import { useStyles } from './RunDebriefStyles';

export const RunDebriefHeader = ({ run }: { run: TestRun }) => {
  const { classes, cx } = useStyles();
  const applications = useAtomValue(applicationsAtom);

  return (
    <>
      <div className={classes.eyebrow}>{he.panel.runDebrief}</div>
      <div className={classes.titleRow}>
        <IdentityDot color={resolveScopeColor(applications, run.applicationId)} />
        <span className={classes.title}>{run.scopeLabel}</span>
        {/* <StatusBadge status={run.status} /> */}
      </div>
      <div className={cx(classes.subtitle, 'num')}>
        {run.testName} · {formatShortDate(run.startedAt)} {he.panel.at}{' '}
        {formatTime(run.startedAt)}
      </div>
    </>
  );
};

/**
 * Imperative actions exposed to the panel footer in App.tsx, which renders
 * the "הורדת דוח" button alongside "סגירה". A ref rather than lifting the
 * comments/artifacts fetch up to App.tsx: this component already owns that
 * data, so the footer only needs to trigger the one action, not duplicate
 * the fetching.
 */
export interface RunDebriefHandle {
  /** Builds the full debrief as plain Hebrew text and downloads it. */
  downloadReport: () => void;
}

export const RunDebrief = forwardRef<RunDebriefHandle, { run: TestRun }>(({ run }, ref) => {
  const { classes, cx } = useStyles();
  const pushToast = useSetAtom(pushToastAtom);

  const [draft, setDraft] = useState('');
  const [authorName, setAuthorName] = useState('');
  const [isPosting, setIsPosting] = useState(false);
  const [artifacts, setArtifacts] = useState<RunArtifact[]>([]);

  const { data: comments, reload: reloadComments } = useRunComments(run.id);

  const [copiedId, setCopiedId] = useState<string | null>(null);

  const isId = (value: string) =>
    /^[a-z0-9]+-[a-z0-9-]+$/.test(value);

  const handleCopy = async (value: string) => {
    await navigator.clipboard.writeText(value);
    setCopiedId(value);

    setTimeout(() => {
      setCopiedId(null);
    }, 1500);
  };

  // Presigned URLs are short-lived, so artifacts are fetched when opened.
  useEffect(() => {
    if (run.artifactCount === 0) {
      setArtifacts([]);
      return;
    }

    let cancelled = false;
    runService
      .listArtifacts(run.id)
      .then((result) => {
        if (!cancelled) setArtifacts(result);
      })
      .catch(() => {
        if (!cancelled) setArtifacts([]);
      });

    return () => {
      cancelled = true;
    };
  }, [run.id, run.artifactCount]);

  const submitComment = async () => {
    const body = draft.trim();
    if (!body || isPosting) return;

    setIsPosting(true);
    try {
      await runService.addComment(run.id, body, authorName.trim() || he.panel.anonymous);
      setDraft('');
      reloadComments();
    } catch {
      pushToast({ message: he.errors.generic, severity: 'error' });
    } finally {
      setIsPosting(false);
    }
  };

  const metaFields: Array<[string, string]> = [
    [he.panel.startedAt, formatTime(run.startedAt)],
    [he.panel.endedAt, run.endedAt ? formatTime(run.endedAt) : '—'],
    [he.panel.duration, formatDuration(run.durationSeconds)],
    [he.panel.runBy, run.triggeredBy],
    [he.panel.runId, run.id],
    [he.timeline.columns.status, run.status]
  ];

  const screenshots = artifacts.filter((artifact) => artifact.kind === 'screenshot');
  // Chronological (oldest first) — this is what the count and the downloaded
  // report use, since a report reads top-to-bottom like a log.
  const commentList = comments ?? [];
  // The on-screen thread reads newest-first instead, so the latest note is
  // the one visible without scrolling.
  const visibleComments = [...commentList].reverse();

  // Renders everything the panel shows above the footer as plain text, in the
  // same top-to-bottom order, then triggers the browser download directly —
  // the footer button just calls this, it never touches the data itself.
  useImperativeHandle(
    ref,
    () => ({
      downloadReport: () => {
        const lines: string[] = [];

        lines.push(he.panel.runDebrief);
        lines.push(`${run.scopeLabel} · ${run.testName}`);
        lines.push(
          `${formatShortDate(run.startedAt)} ${he.panel.at} ${formatTime(run.startedAt)}`,
        );
        lines.push('');

        lines.push(`-- ${he.report.details} --`);
        lines.push(`${he.panel.startedAt}: ${formatTime(run.startedAt)}`);
        lines.push(`${he.panel.endedAt}: ${run.endedAt ? formatTime(run.endedAt) : '—'}`);
        lines.push(`${he.panel.duration}: ${formatDuration(run.durationSeconds)}`);
        lines.push(`${he.panel.runBy}: ${run.triggeredBy}`);
        lines.push(`${he.panel.runId}: ${run.id}`);
        lines.push(`${he.report.status}: ${he.status[run.status]}`);
        lines.push('');

        if (run.failure) {
          lines.push(`-- ${he.panel.whatWentWrong} --`);
          lines.push(`${run.failure.errorType} ב${run.failure.feature}`);
          lines.push(run.failure.reason);
          lines.push('');
        }

        if (run.artifactCount > 0) {
          lines.push(`-- ${he.panel.screenshots} --`);
          if (screenshots.length > 0) {
            screenshots.forEach((artifact) => lines.push(`- ${artifact.fileName}`));
          } else {
            lines.push('—');
          }
          lines.push('');
        }

        lines.push(`-- ${he.panel.comments} (${commentList.length}) --`);
        if (commentList.length > 0) {
          commentList.forEach((comment) => {
            lines.push(`[${comment.authorName}] ${formatTime(comment.createdAt)}`);
            lines.push(comment.body);
            lines.push('');
          });
        } else {
          lines.push(he.report.noComments);
        }

        // A BOM, matching the CSV export in runRoutes: without it some
        // Windows text editors misread UTF-8 Hebrew as another encoding.
        const blob = new Blob(['\ufeff', lines.join('\n')], {
          type: 'text/plain;charset=utf-8',
        });
        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = url;
        link.download = `דוח-ריצה-${run.id}.txt`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        URL.revokeObjectURL(url);
      },
    }),
    [run, commentList, screenshots],
  );

  return (
    <div className={classes.root}>
      <div className={classes.metaGrid}>
        {metaFields.map(([label, value]) => (
          <div key={label} className={classes.metaCell}>
            <div className={classes.metaLabel}>{label}</div>

            {['passed', 'failed', 'cancelled'].includes(value) ? (
              <StatusBadge status={value as 'passed' | 'failed' | 'cancelled'} />
            ) : isId(value) ? (
              <div className={classes.idValue}>
                <div className={cx(classes.metaValue, 'num')}>
                  {value}
                </div>
                <Tooltip
                  title="Copied!"
                  placement="top"
                  open={copiedId === value}
                >
                  <IconButton
                    size="small"
                    onClick={() => void handleCopy(value)}
                  >
                    <ContentCopyIcon fontSize="small" />
                  </IconButton>
                </Tooltip>


              </div>
            ) : (
              <div className={cx(classes.metaValue, 'num')}>
                {value}
              </div>
            )}
          </div>
        ))}

      </div>


      {run.failure && (
        <section>
          <h3 className={classes.sectionTitle}>{he.panel.whatWentWrong}</h3>
          <div className={classes.callout}>
            <span className={classes.calloutIcon}>
              <WarningIcon fontSize="inherit" />
            </span>
            <div>
              <div className={classes.calloutHeading}>
                {run.failure.errorType} ב{run.failure.feature}
              </div>
              {run.failure.reason}
            </div>
          </div>
        </section>
      )}

      {run.artifactCount > 0 && (
        <section>
          <h3 className={classes.sectionTitle}>{he.panel.screenshots}</h3>
          <div className={classes.shotGrid}>
            {screenshots.length > 0 ? (
              screenshots
                .filter((artifact) => artifact.downloadUrl !== null)
                .map((artifact) => (
                  <div key={artifact.id} className={classes.shot}>
                    <img
                      src={artifact.downloadUrl as string}
                      alt={artifact.fileName}
                      loading="lazy"
                    />
                  </div>
                ))
            ) : (
              <div className={classes.shot}>
                <ImageIcon fontSize="inherit" />
              </div>
            )}
          </div>
        </section>
      )}
      

      <section>
        <h3 className={classes.sectionTitle}>
          {he.panel.comments} <span className="num">({commentList.length})</span>
        </h3>

        <div className={classes.composer}>
          {/* <TextField
            className={classes.authorInput}
            size="small"
            value={authorName}
            placeholder={he.panel.authorPlaceholder}
            onChange={(event) => setAuthorName(event.target.value)}
            inputProps={{ maxLength: 120 }}
          /> */}

          <div className={classes.composerRow}>
            <TextField
              className={classes.composerInput}
              size="small"
              multiline
              value={draft}
              placeholder={he.panel.commentPlaceholder}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  void submitComment();
                }
              }}
            />
            <Button
              variant="primary"
              onClick={() => void submitComment()}
              disabled={!draft.trim() || isPosting}
            >
              <SendIcon sx={{ fontSize: 15 }} />
              {he.actions.send}
            </Button>
          </div>
        </div>

        {commentList.length > 0 ? (
          <div className={classes.thread}>
            {visibleComments.map((comment) => (
              <div key={comment.id} className={classes.comment}>
                <Avatar className={classes.avatar}>{initials(comment.authorName)}</Avatar>
                <div className={classes.commentBody}>
                  <div className={classes.commentHead}>
                    <span className={classes.commentAuthor}>{comment.authorName}</span>
                    <span className={cx(classes.commentTime, 'num')}>
                      {formatTime(comment.createdAt)}
                    </span>
                  </div>
                  <div className={classes.commentText}>{comment.body}</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className={classes.emptyNote}>{he.panel.noComments}</div>
        )}
      </section>
    </div>
  );
});

RunDebrief.displayName = 'RunDebrief';
