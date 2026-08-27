import CheckCircleIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorIcon from '@mui/icons-material/ErrorOutline';
import PendingIcon from '@mui/icons-material/ScheduleOutlined';
import CancelIcon from '@mui/icons-material/RemoveCircleOutline';
import LoaderIcon from '@mui/icons-material/AutorenewOutlined';
import { he } from '@/locales/he';
import type { TestDisplayStatus } from '@/types/run.types';
import { useStyles } from './StatusBadgeStyles';

export interface StatusBadgeProps {
  status: TestDisplayStatus;
}

export const StatusBadge = ({ status }: StatusBadgeProps) => {
  const { classes } = useStyles({ status });

  const renderIcon = () => {
    const size = { fontSize: 13 };

    switch (status) {
      case 'passed':
        return <CheckCircleIcon sx={size} />;
      case 'failed':
      case 'timed_out':
        return <ErrorIcon sx={size} />;
      case 'cancelled':
        return <CancelIcon sx={size} />;
      case 'running':
      case 'queued':
        return (
          <span className={classes.spinner}>
            <LoaderIcon sx={size} />
          </span>
        );
      default:
        return <PendingIcon sx={size} />;
    }
  };

  return (
    <span className={classes.root} data-testid="status-badge">
      {renderIcon()}
      {he.status[status]}
    </span>
  );
};
