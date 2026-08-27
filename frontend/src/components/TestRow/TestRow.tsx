import { Tooltip } from '@mui/material';
import PlayIcon from '@mui/icons-material/PlayArrowRounded';
import StopIcon from '@mui/icons-material/StopRounded';
import WarningIcon from '@mui/icons-material/WarningAmberRounded';
import { Button } from '@/components/Button/Button';
import { IdentityDot } from '@/components/IdentityDot/IdentityDot';
import { StatusBadge } from '@/components/StatusBadge/StatusBadge';
import { he } from '@/locales/he';
import type { TestDefinition } from '@/types/application.types';
import type { TestDisplayStatus } from '@/types/run.types';
import { formatDuration, formatElapsed, formatTime } from '@/utils/format';
import { useStyles } from './TestRowStyles';

export interface TestRowProps {
  definition: TestDefinition;
  color: string;
  status: TestDisplayStatus;
  elapsedSeconds: number;
  durationSeconds: number | null;
  endedAt: string | null;
  failureReason: string | null;
  canRun: boolean;
  onRun: () => void;
  onStop: () => void;
}

export const TestRow = ({
  definition,
  color,
  status,
  elapsedSeconds,
  durationSeconds,
  endedAt,
  failureReason,
  canRun,
  onRun,
  onStop,
}: TestRowProps) => {
  const isMain = definition.kind === 'main';
  const { classes, cx } = useStyles({ emphasised: isMain });
  const inFlight = status === 'running' || status === 'queued';

  const buildMeta = (): string => {
    if (inFlight) return `${he.status.running} · ${formatElapsed(elapsedSeconds)}`;
    if (status === 'idle') return he.tests.notRunThisSession;

    const label = he.status[status];
    const time = endedAt ? formatTime(endedAt) : '—';
    return `${label} ב-${time} · ${formatDuration(durationSeconds)}`;
  };

  return (
    <div
      className={classes.root}
      data-testid={isMain ? 'test-row-main' : `test-row-${definition.name}`}
    >
      <IdentityDot color={color} live={inFlight} />

      <div className={classes.main}>
        <div className={classes.name}>{definition.name}</div>
        <div className={cx(classes.meta, 'num')}>{buildMeta()}</div>
      </div>

      {failureReason && !inFlight && (
        <Tooltip title={failureReason}>
          <span className={classes.warning}>
            <WarningIcon fontSize="inherit" />
          </span>
        </Tooltip>
      )}

      <StatusBadge status={status} />

      {inFlight ? (
        <Button variant="danger" size="small" onClick={onStop} disabled={!canRun} data-testid="stop-button">
          <StopIcon sx={{ fontSize: 14 }} />
          {he.actions.stop}
        </Button>
      ) : (
        <Tooltip title={canRun ? '' : he.tests.noPermission}>
          <span>
            <Button
              variant={isMain ? 'primary' : 'ghost'}
              size="small"
              onClick={onRun}
              disabled={!canRun}
              data-testid="run-button"
            >
              <PlayIcon sx={{ fontSize: 14 }} />
              {he.actions.run}
            </Button>
          </span>
        </Tooltip>
      )}
    </div>
  );
};
