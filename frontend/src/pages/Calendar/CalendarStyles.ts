import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

export const useStyles = makeStyles()(() => ({
  card: {
    overflow: 'hidden',
    borderRadius: tokens.radius.card,
    background: tokens.color.surface,
    border: '1px solid rgba(10,36,78,.05)',
    boxShadow: tokens.shadow.sm,
  },
  toolbar: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    flexWrap: 'wrap',
    padding: '14px 18px',
  },
  monthTitle: {
    fontSize: tokens.font.size.lg,
    fontWeight: tokens.font.weight.bold,
    letterSpacing: '-.022em',
  },
  subtitle: {
    fontSize: tokens.font.size.sm,
    color: tokens.color.ink40,
  },
  spacer: { flex: 1 },
  navGroup: { display: 'flex', gap: 4 },

  jumpGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
  },
  jumpTrigger: {
    border: 0,
    borderRadius: tokens.radius.sm,
    background: tokens.color.tintSoft,
    padding: '7px 11px',
    font: 'inherit',
    fontSize: tokens.font.size.sm,
    fontWeight: tokens.font.weight.semibold,
    color: tokens.color.ink,
    cursor: 'pointer',
    '&:hover': { backgroundColor: tokens.color.runningBg },
    '&:focus-visible': { outline: `2px solid ${tokens.color.running}` },
  },
  /**
   * The month and year popups.
   *
   * A top-level class, not nested under another rule: this popup is portalled
   * to the document root, so it is never a descendant of anything on the page.
   */
  jumpMenu: {
    minWidth: 220,
    maxHeight: 320,
    overflowY: 'auto',
    padding: 10,
    border: `1px solid ${tokens.color.lineStrong}`,
    borderRadius: tokens.radius.control,
    boxShadow: tokens.shadow.md,
    backgroundColor: tokens.color.surface,

    '& .calendar-jump-month-grid, & .calendar-jump-year-list': {
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 1fr)',
      gap: 4,
    },

    '& button': {
      minHeight: 36,
      border: '1.5px solid transparent',
      borderRadius: tokens.radius.sm,
      background: 'transparent',
      color: tokens.color.ink,
      cursor: 'pointer',
      font: 'inherit',
      fontSize: tokens.font.size.sm,
      '&:hover:not(:disabled)': { backgroundColor: tokens.color.runningBg },
      // Today gets an outline only, so it never competes with the selection.
      '&[data-today]': { borderColor: tokens.color.running },
      '&.is-selected': {
        backgroundColor: tokens.color.running,
        color: tokens.color.surface,
        fontWeight: tokens.font.weight.semibold,
        borderColor: 'transparent',
      },
      '&:disabled': {
        color: tokens.color.ink25,
        cursor: 'default',
        pointerEvents: 'none',
      },
      '&:focus-visible': { outline: `2px solid ${tokens.color.running}` },
    },
  },

  /** Grid items flow right-to-left under RTL, so Sunday lands on the right. */
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(7, 1fr)',
  },
  gridBorder: { borderTop: `1px solid ${tokens.color.line}` },

  headerCell: {
    padding: '10px 12px',
    fontSize: tokens.font.size.xs,
    fontWeight: 640,
    color: tokens.color.ink40,
    textAlign: 'start',
  },

  day: {
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'stretch',
    gap: 4,
    minHeight: 118,
    padding: 8,
    textAlign: 'start',
    borderTop: `1px solid ${tokens.color.line}`,
    borderInlineStart: `1px solid ${tokens.color.line}`,
    transition: 'background .18s',
    '&:nth-of-type(7n + 1)': { borderInlineStart: 0 },
    '&:hover:not(.Mui-disabled)': { background: tokens.color.tintSoft },
  },

  padCell: {
    minHeight: 118,
    borderTop: `1px solid ${tokens.color.line}`,
    borderInlineStart: `1px solid ${tokens.color.line}`,
    background: 'rgba(10,36,78,.012)',
    '&:nth-of-type(7n + 1)': { borderInlineStart: 0 },
  },

  dayHead: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
  },
  dayNumber: {
    display: 'grid',
    placeItems: 'center',
    width: 23,
    height: 23,
    borderRadius: '50%',
    fontSize: tokens.font.size.sm,
    fontWeight: tokens.font.weight.medium,
    color: tokens.color.ink60,
  },
  dayNumberToday: {
    color: '#fff',
    background: tokens.color.ink,
  },
  dayNumberFuture: {
    color: tokens.color.ink25,
    fontWeight: 450,
  },
  failedCount: {
    fontSize: 10.5,
    fontWeight: 600,
    color: tokens.color.fail,
  },

  chip: {
    display: 'flex',
    alignItems: 'center',
    gap: 5,
    padding: '3px 6px',
    borderRadius: 6,
    background: 'rgba(10,36,78,.045)',
    fontSize: 11,
    fontWeight: tokens.font.weight.medium,
    overflow: 'hidden',
  },
  chipBar: {
    width: 3,
    height: 11,
    borderRadius: 2,
    flexShrink: 0,
  },
  chipLabel: {
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    color: tokens.color.ink80,
  },
  chipStatus: {
    marginInlineStart: 'auto',
    width: 5,
    height: 5,
    borderRadius: '50%',
    flexShrink: 0,
  },
  more: {
    paddingInlineStart: 6,
    fontSize: 11,
    fontWeight: tokens.font.weight.medium,
    color: tokens.color.ink40,
  },
}));