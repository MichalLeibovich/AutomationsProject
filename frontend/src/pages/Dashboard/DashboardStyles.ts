import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

export const useStyles = makeStyles()(() => ({
  root: {
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
  },
  toolbar: {
    display: 'flex',
    alignItems: 'center',
    gap: 14,
    flexWrap: 'nowrap',
    height: 84,
    boxSizing: 'border-box',
    padding: '13px 18px',
    borderRadius: tokens.radius.card,
    background: tokens.color.surface,
    border: '1px solid rgba(10,36,78,.05)',
    boxShadow: tokens.shadow.sm,
  },
  title: {
    fontSize: tokens.font.size.md,
    fontWeight: tokens.font.weight.semibold,
  },
  subtitle: {
    fontSize: tokens.font.size.sm,
    color: tokens.color.ink40,
  },
  spacer: { flex: 1 },
  customRange: {
    display: 'flex',
    alignItems: 'center',
    flexWrap: 'nowrap',
    gap: 10,
  },

  field: {
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
  },

  fieldLabel: {
    position: 'absolute',
    insetInlineEnd: 0,
    bottom: '100%',
    marginBottom: 3,
    fontSize: 11,
    fontWeight: 600,
    color: tokens.color.ink60,
    whiteSpace: 'nowrap',
  },

  rangeDash: {
    color: tokens.color.ink60,
    alignSelf: 'center',
  },

  /**
   * Takes the whole row so the controls never shift sideways when a message
   * appears — a moving apply button is easy to misclick.
   */
  rangeError: {
    flexBasis: '100%',
    fontSize: 11,
    fontWeight: 600,
    color: tokens.color.fail,
  },
  dateInput: {
    '& .MuiOutlinedInput-root': {
      borderRadius: tokens.radius.sm,
      background: tokens.color.tintSoft,
      fontSize: tokens.font.size.sm,
      '& fieldset': { border: 0 },
      '&.Mui-focused': { boxShadow: `inset 0 0 0 1.5px ${tokens.color.running}` },
    },
    '& .MuiOutlinedInput-input': { padding: '7px 11px' },
  },
  datePickerPaper: {
    overflow: 'hidden',
    border: `1px solid ${tokens.color.lineStrong}`,
    borderRadius: tokens.radius.card,
    boxShadow: tokens.shadow.md,
    '& .dashboard-date-picker-header': {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '8px 12px 4px',
    },
    '& .dashboard-date-picker-heading': {
      display: 'flex',
      alignItems: 'center',
      gap: 4,
    },
    '& .dashboard-date-picker-heading button': {
      border: 0,
      borderRadius: tokens.radius.sm,
      padding: '6px 8px',
      background: 'transparent',
      color: tokens.color.ink,
      cursor: 'pointer',
      font: 'inherit',
      fontSize: tokens.font.size.sm,
      fontWeight: tokens.font.weight.semibold,
      '&:hover': { backgroundColor: tokens.color.runningBg },
      '&:focus-visible': { outline: `2px solid ${tokens.color.running}` },
    },
    '& .dashboard-date-picker-menu': {
      minWidth: 220,
      maxHeight: 300,
      padding: 10,
      border: `1px solid ${tokens.color.lineStrong}`,
      borderRadius: tokens.radius.control,
      boxShadow: tokens.shadow.md,
      backgroundColor: tokens.color.surface,
    },
    '& .dashboard-date-picker-month-grid': {
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 1fr)',
      gap: 4,
    },
    '& .dashboard-date-picker-year-list': {
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 1fr)',
      gap: 4,
      maxHeight: 260,
      overflowY: 'auto',
    },
    '& .dashboard-date-picker-month-grid button, & .dashboard-date-picker-year-list button': {
      minHeight: 36,
      border: 0,
      borderRadius: tokens.radius.sm,
      background: 'transparent',
      color: tokens.color.ink,
      cursor: 'pointer',
      font: 'inherit',
      fontSize: tokens.font.size.sm,
      '&:hover': { backgroundColor: tokens.color.runningBg },
      '&.is-selected': {
        backgroundColor: tokens.color.running,
        color: tokens.color.surface,
        fontWeight: tokens.font.weight.semibold,
      },
      '&:focus-visible': { outline: `2px solid ${tokens.color.running}` },
    },
    '& .MuiDateCalendar-root': {
      width: 320,
      maxHeight: 'none',
      paddingBottom: 8,
    },
    '& .MuiDayCalendar-header': {
      justifyContent: 'space-around',
      paddingInline: 10,
    },
    '& .MuiDayCalendar-weekDayLabel': {
      color: tokens.color.ink40,
      fontSize: 11,
      fontWeight: 600,
    },
    '& .MuiPickersDay-root': {
      fontSize: 12,
      '&.Mui-selected': {
        backgroundColor: tokens.color.running,
        color: tokens.color.surface,
        '&:hover': { backgroundColor: tokens.color.running },
      },
      '&:hover': { backgroundColor: tokens.color.runningBg },
    },
    '& .MuiPickersArrowSwitcher-button': {
      color: tokens.color.ink60,
      '&:hover': { backgroundColor: tokens.color.runningBg },
    },
  },
  stats: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))',
    gap: 14,
  },
  chartPair: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
    gap: 16,
  },
  donutWrap: {
    display: 'flex',
    alignItems: 'center',
    height: '100%',
    gap: 10,
  },
  donut: {
    position: 'relative',
    width: 190,
    height: '100%',
    flexShrink: 0,
  },
  donutCentre: {
    position: 'absolute',
    inset: 0,
    display: 'grid',
    placeItems: 'center',
    pointerEvents: 'none',
    textAlign: 'center',
  },
  donutTotal: {
    fontSize: 25,
    fontWeight: tokens.font.weight.bold,
    letterSpacing: '-.03em',
  },
  legend: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
    paddingBottom: 8,
  },
  legendRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    fontSize: tokens.font.size.sm,
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: '50%',
    flexShrink: 0,
  },
  legendName: { flex: 1 },
  legendCount: { fontWeight: 600 },
  emptyCard: {
    borderRadius: tokens.radius.card,
    background: tokens.color.surface,
    border: '1px solid rgba(10,36,78,.05)',
    boxShadow: tokens.shadow.sm,
  },
}));
