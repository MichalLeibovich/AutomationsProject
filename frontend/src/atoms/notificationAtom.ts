import { atom } from 'jotai';

/** Mirrors the browser's Notification permission, plus `unsupported` for a
 * browser that has no Notification API at all (the failure sound still works
 * either way — see utils/sound.ts). */
export type NotificationPermissionState = 'default' | 'granted' | 'denied' | 'unsupported';

const readPermission = (): NotificationPermissionState => {
  if (typeof window === 'undefined' || !('Notification' in window)) return 'unsupported';
  return Notification.permission;
};

/** Read once at module load. The only thing that can change it afterwards is
 * the user's own click, handled by {@link requestNotificationPermissionAtom},
 * which updates this directly — there is no browser event to listen for. */
export const notificationPermissionAtom = atom<NotificationPermissionState>(readPermission());

/** Requests permission. Only meaningful, and only ever called, from a click —
 * browsers require a user gesture for the prompt to appear at all. */
export const requestNotificationPermissionAtom = atom(null, async (_get, set) => {
  if (typeof window === 'undefined' || !('Notification' in window)) return;

  const result = await Notification.requestPermission();
  set(notificationPermissionAtom, result);
});
