import { atom } from 'jotai';

export type ToastSeverity = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: number;
  message: string;
  severity: ToastSeverity;
}

export const TOAST_DURATION_MS = 2600;

export const toastsAtom = atom<Toast[]>([]);

let nextId = 0;

export const pushToastAtom = atom(
  null,
  (get, set, payload: { message: string; severity?: ToastSeverity }) => {
    const toast: Toast = {
      id: ++nextId,
      message: payload.message,
      severity: payload.severity ?? 'info',
    };
    set(toastsAtom, [...get(toastsAtom), toast]);

    setTimeout(() => {
      set(
        toastsAtom,
        get(toastsAtom).filter((entry) => entry.id !== toast.id),
      );
    }, TOAST_DURATION_MS);
  },
);

export const dismissToastAtom = atom(null, (get, set, id: number) => {
  set(
    toastsAtom,
    get(toastsAtom).filter((entry) => entry.id !== id),
  );
});
