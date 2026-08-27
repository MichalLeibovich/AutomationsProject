import { useMemo } from 'react';
import { useAtomValue, useSetAtom } from 'jotai';
import { ButtonBase } from '@mui/material';
import ChevronForwardIcon from '@mui/icons-material/ChevronLeftRounded';
import { IdentityDot } from '@/components/IdentityDot/IdentityDot';
import { StatusBadge } from '@/components/StatusBadge/StatusBadge';
import { applicationsAtom } from '@/atoms/appAtom';
import { pushRunPanelAtom } from '@/atoms/panelAtom';
import { he } from '@/locales/he';
import type { TestRun } from '@/types/run.types';
import { formatDuration, formatLongDate, formatTime } from '@/utils/format';
import { resolveScopeColor } from '@/utils/scope';
import { useStyles } from './DayDetailStyles';

export interface DayDetailProps {
  runs: TestRun[];
}

export const DayDetailHeader = ({ date, runs }: { date: string; runs: TestRun[] }) => {
  const { classes, cx } = useStyles();
  const failed = runs.filter((run) => run.status === 'failed').length;

  return (
    <>
      <div className={classes.eyebrow}>{he.panel.dayDetail}</div>
      <div className={classes.title}>{formatLongDate(date)}</div>
      <div className={cx(classes.summary, 'num')}>
        {he.panel.daySummary(runs.length, runs.length - failed, failed)}
      </div>
    </>
  );
};

/**
 * Runs grouped onto an hour rail. Clicking one pushes it onto the panel stack
 * rather than opening a second overlay.
 */
export const DayDetail = ({ runs }: DayDetailProps) => {
  const { classes, cx } = useStyles();
  const applications = useAtomValue(applicationsAtom);
  const pushRun = useSetAtom(pushRunPanelAtom);

  const byHour = useMemo(() => {
    const groups = new Map<number, TestRun[]>();

    for (const run of runs) {
      const hour = new Date(run.startedAt).getHours();
      const bucket = groups.get(hour) ?? [];
      bucket.push(run);
      groups.set(hour, bucket);
    }

    return [...groups.entries()].sort(([a], [b]) => a - b);
  }, [runs]);

  return (
    <div className={classes.list}>
      {byHour.map(([hour, items]) => (
        <div key={hour} className={classes.hourGroup}>
          <div className={cx(classes.hourLabel, 'num')}>
            {String(hour).padStart(2, '0')}:00
          </div>

          <div className={classes.runs}>
            {items.map((run) => (
              <ButtonBase key={run.id} className={classes.run} onClick={() => pushRun(run)}>
                <IdentityDot color={resolveScopeColor(applications, run.applicationId)} />

                <div className={classes.runText}>
                  <div className={classes.runName}>{run.scopeLabel}</div>
                  <div className={cx(classes.runMeta, 'num')}>
                    {run.testName} · {formatTime(run.startedAt)} ·{' '}
                    {formatDuration(run.durationSeconds)}
                  </div>
                </div>

                <StatusBadge status={run.status} />
                <span className={classes.chevron}>
                  <ChevronForwardIcon fontSize="inherit" />
                </span>
              </ButtonBase>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};
