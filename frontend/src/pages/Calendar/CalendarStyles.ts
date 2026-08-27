import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

export const useStyles = makeStyles()(() => ({
  card: {
    height: '100%',
    maxHeight: '100%',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
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
    flexShrink: 0,
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

  spacer: {
    flex: 1,
  },

  navGroup: {
    display: 'flex',
    gap: 4,
  },

  /**
   * Calendar weekday header.
   */
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(7, 1fr)',
  },

  /**
   * The actual calendar days.
   *
   * A month can occupy up to 6 rows.
   * Every row gets exactly the same height.
   */
  dayGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(7, 1fr)',
    gridTemplateRows: 'repeat(6, minmax(0, 1fr))',
    flex: 1,
    minHeight: 0,
  },

  gridBorder: {
    borderTop: `1px solid ${tokens.color.line}`,
    flexShrink: 0,
  },

  headerCell: {
    padding: '8px 12px',
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
    gap: 3,

    /*
     * Important:
     * Don't let the content determine the height.
     */
    minHeight: 0,
    height: '100%',
    minWidth: 0,

    padding: 7,
    textAlign: 'start',

    borderTop: `1px solid ${tokens.color.line}`,
    borderInlineStart: `1px solid ${tokens.color.line}`,

    transition: 'background .18s',
    overflow: 'hidden',

    '&:nth-of-type(7n + 1)': {
      borderInlineStart: 0,
    },

    '&:hover:not(.Mui-disabled)': {
      background: tokens.color.tintSoft,
    },
  },

  padCell: {
    minHeight: 0,
    height: '100%',
    minWidth: 0,

    borderTop: `1px solid ${tokens.color.line}`,
    borderInlineStart: `1px solid ${tokens.color.line}`,
    background: 'rgba(10,36,78,.012)',

    '&:nth-of-type(7n + 1)': {
      borderInlineStart: 0,
    },
  },

  dayHead: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    flexShrink: 0,
  },

  dayNumber: {
    display: 'grid',
    placeItems: 'center',
    width: 23,
    height: 23,
    flexShrink: 0,
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
    minWidth: 0,
    minHeight: 0,

    padding: '2px 5px',
    borderRadius: 6,
    background: 'rgba(10,36,78,.045)',

    fontSize: 10.5,
    fontWeight: tokens.font.weight.medium,

    overflow: 'hidden',
    flexShrink: 0,
  },

  chipBar: {
    width: 3,
    height: 10,
    borderRadius: 2,
    flexShrink: 0,
  },

  chipLabel: {
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    color: tokens.color.ink80,
    minWidth: 0,
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
    fontSize: 10.5,
    fontWeight: tokens.font.weight.medium,
    color: tokens.color.ink40,
    flexShrink: 0,
  },
}));