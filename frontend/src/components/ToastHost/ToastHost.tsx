import { useAtomValue } from 'jotai';
import { Fade } from '@mui/material';
import CheckIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorIcon from '@mui/icons-material/ErrorOutline';
import WarningIcon from '@mui/icons-material/WarningAmberOutlined';
import InfoIcon from '@mui/icons-material/InfoOutlined';
import { toastsAtom } from '@/atoms/toastAtom';
import type { ToastSeverity } from '@/atoms/toastAtom';
import { useStyles } from './ToastHostStyles';

const ICONS: Record<ToastSeverity, typeof InfoIcon> = {
  success: CheckIcon,
  error: ErrorIcon,
  warning: WarningIcon,
  info: InfoIcon,
};

/**
 * Renders the toast queue. Mounted once at the app root; anything can queue a
 * toast by writing to `pushToastAtom` without prop-drilling a handler.
 */
export const ToastHost = () => {
  const { classes } = useStyles();
  const toasts = useAtomValue(toastsAtom);

  if (toasts.length === 0) return null;

  return (
    <div className={classes.stack} role="status" aria-live="polite">
      {toasts.map((toast) => {
        const Icon = ICONS[toast.severity];

        return (
          <Fade in key={toast.id}>
            <div className={classes.toast} data-testid="toast">
              <span className={classes.icon}>
                <Icon fontSize="inherit" />
              </span>
              {toast.message}
            </div>
          </Fade>
        );
      })}
    </div>
  );
};
