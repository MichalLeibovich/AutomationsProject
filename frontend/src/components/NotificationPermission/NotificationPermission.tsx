import { useAtomValue, useSetAtom } from 'jotai';
import { Tooltip } from '@mui/material';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActiveOutlined';
import NotificationsOffIcon from '@mui/icons-material/NotificationsOffOutlined';
import NotificationsNoneIcon from '@mui/icons-material/NotificationsNoneOutlined';
import { Button } from '@/components/Button/Button';
import { notificationPermissionAtom, requestNotificationPermissionAtom } from '@/atoms/notificationAtom';
import { he } from '@/locales/he';
import { useStyles } from './NotificationPermissionStyles';

/**
 * A single small, always-present control for granting desktop-notification
 * permission — nothing more. It does not manage notifications themselves
 * (that lives in useScheduleFailureNotifications, mounted separately at the
 * app shell so it works regardless of which page is open); this is only the
 * one clear way to grant the browser permission that control depends on.
 *
 * Unsupported browsers render nothing: there is nothing to grant.
 */
export const NotificationPermission = () => {
  const { classes } = useStyles();
  const permission = useAtomValue(notificationPermissionAtom);
  const requestPermission = useSetAtom(requestNotificationPermissionAtom);

  if (permission === 'unsupported') return null;

  const label =
    permission === 'granted'
      ? he.notifications.permissionGranted
      : permission === 'denied'
        ? he.notifications.permissionDenied
        : he.notifications.permissionDefault;

  const icon =
    permission === 'granted' ? (
      <NotificationsActiveIcon className={classes.granted} sx={{ fontSize: 18 }} />
    ) : permission === 'denied' ? (
      <NotificationsOffIcon className={classes.denied} sx={{ fontSize: 18 }} />
    ) : (
      <NotificationsNoneIcon sx={{ fontSize: 18 }} />
    );

  return (
    <Tooltip title={label}>
      <span>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => void requestPermission()}
          disabled={permission !== 'default'}
          aria-label={he.notifications.permissionButtonLabel}
          data-testid="notification-permission-button"
        >
          {icon}
        </Button>
      </span>
    </Tooltip>
  );
};
