import { useEffect, useState } from 'react';
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

export const RunDebrief = ({ run }: { run: TestRun }) => {
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
  const commentList = comments ?? [];


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

        {commentList.length > 0 ? (
          <div className={classes.thread}>
            {commentList.map((comment) => (
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
      </section>
    </div>
  );
};
