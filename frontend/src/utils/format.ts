import { LOCALE } from './constants';

const toDate = (value: string | Date): Date => (value instanceof Date ? value : new Date(value));

/** "8 דק׳ 30 שנ׳" — the single duration formatter for the whole app. */
export const formatDuration = (seconds: number | null | undefined): string => {
  if (seconds == null) return '—';
  if (seconds < 60) return `${seconds}s`;
  return `${Math.floor(seconds / 60)}m ${seconds % 60} seconds`;
};

/** "0:07" — for the live elapsed counter. */
export const formatElapsed = (seconds: number): string =>
  `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;

export const formatTime = (value: string | Date): string =>
  toDate(value).toLocaleTimeString(LOCALE, { hour: '2-digit', minute: '2-digit', hour12: false });

export const formatShortDate = (value: string | Date): string =>
  toDate(value).toLocaleDateString(LOCALE, { weekday: 'short', month: 'short', day: 'numeric' });

export const formatLongDate = (value: string | Date): string =>
  toDate(value).toLocaleDateString(LOCALE, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });

export const formatMonthYear = (value: Date): string =>
  value.toLocaleDateString(LOCALE, { month: 'long', year: 'numeric' });

export const formatNumber = (value: number): string => value.toLocaleString(LOCALE);

export const initials = (name: string): string =>
  name
    .split(' ')
    .map((word) => word[0] ?? '')
    .slice(0, 2)
    .join('');

/** Stable YYYY-M-D key used to bucket runs into days. */
export const dayKey = (value: string | Date): string => {
  const date = toDate(value);
  return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
};

/** ISO date (YYYY-MM-DD) in local time, for date inputs and query params. */
export const toIsoDate = (value: Date): string => {
  const offset = value.getTimezoneOffset() * 60_000;
  return new Date(value.getTime() - offset).toISOString().slice(0, 10);
};
