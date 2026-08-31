import { useEffect, useRef } from 'react';
import { useAtomValue } from 'jotai';
import { notificationPermissionAtom } from '@/atoms/notificationAtom';
import { scheduleFailureEventAtom } from '@/atoms/scheduleFailureAtom';
import { he } from '@/locales/he';
import { playFailureAlert } from '@/utils/sound';

/**
 * Alerts on a scheduled automation's failure, wherever the user currently is
 * in the app — mounted once at the app shell (AppLayout), not on the
 * Scheduled Automations page, precisely so it keeps working regardless of
 * which page is open.
 *
 * The sound and the desktop notification are independent, deliberately: the
 * sound plays every time regardless of Notification permission, since it
 * needs none of its own; the desktop notification is an addition on top,
 * shown only when permission has actually been granted (requested via the
 * small bell control in the navbar, not from here).
 */
export function useScheduleFailureNotifications(): void {
  const event = useAtomValue(scheduleFailureEventAtom);
  const permission = useAtomValue(notificationPermissionAtom);
  const lastHandledRunId = useRef<string | null>(null);

  useEffect(() => {
    if (!event || event.runId === lastHandledRunId.current) return;
    lastHandledRunId.current = event.runId;

    playFailureAlert();

    if (permission === 'granted') {
      // eslint-disable-next-line no-new -- fire-and-forget desktop notification
      new Notification(he.notifications.failureTitle(event.scopeLabel), {
        body: he.notifications.failureBody(event.testName),
      });
    }
  }, [event, permission]);
}
