import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

export const useStyles = makeStyles()(() => ({
  root: {
    display: 'flex',
    flexDirection: 'column',
    gap: 18,
  },

  card: {
    overflow: 'hidden',
    borderRadius: tokens.radius.card,
    background: tokens.color.surface,
    border: '1px solid rgba(10,36,78,.05)',
    boxShadow: tokens.shadow.sm,
    padding: '16px 18px',
  },
  cardHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    marginBottom: 14,
  },
  title: {
    fontSize: tokens.font.size.md,
    fontWeight: tokens.font.weight.semibold,
  },
  spacer: { flex: 1 },
  search: { width: 260 },

  grid: {
    // display: 'grid',
    display: 'flex',
    // gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
    gap: 10,
    justifyContent: "center",
    placeItems: "center",
  },
  tile: {
    display: 'flex',
    width: "15%",
    alignItems: 'center',
    justifyContent: "center",
    gap: 10,
    padding: '12px 14px',
    borderRadius: tokens.radius.control,
    background: tokens.color.canvas,
  },
  tileText: { display: 'flex', flexDirection: 'column', gap: 2, minWidth: 0 },
  tileNameWithDot: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    // minWidth: 0,
  },
  tileName: {
    fontWeight: tokens.font.weight.medium,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  tileTimeWithClock: {
    display: 'flex',
    alignItems: 'center',
    gap: 4,
  },
  tileTime: {
    textAlign: 'center',
    fontSize: tokens.font.size.lg,
    fontWeight: tokens.font.weight.semibold,
    color: tokens.color.ink,
  },

  groupList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
  },
  group: {
    display: 'flex',
    alignItems: 'center',
    gap: 14,
    flexWrap: 'wrap',
    padding: '10px 12px',
    borderRadius: tokens.radius.control,
    background: tokens.color.canvas,
  },
  groupTime: {
    fontWeight: tokens.font.weight.semibold,
    minWidth: 52,
  },
  groupEntries: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    flexWrap: 'wrap',
    flex: 1,
  },
  entry: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    fontSize: tokens.font.size.sm,
  },

  freqGrid: {
    display: 'flex',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 14,
  },
  freqCard: {
    flex: '1 1 200px',
    minWidth: 200,
    maxWidth: 260,
    padding: '18px 20px',
    borderRadius: tokens.radius.control,
    background: tokens.color.canvas,
    border: '1px solid rgba(10,36,78,.05)',
  },
  freqLabel: {
    fontSize: tokens.font.size.xl,
    textAlign: 'center',
    fontWeight: tokens.font.weight.semibold,
    letterSpacing: '-.035em',
    lineHeight: 1.15,
    color: tokens.color.ink,
    marginBottom: 14,
  },
  freqSystems: {
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
  },
  freqSystem: {
    display: 'flex',
    flexDirection: 'column',
    gap: 2,
  },
  freqSystemName: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    fontWeight: tokens.font.weight.semibold,
  },
  freqSystemTest: {
    fontSize: tokens.font.size.sm,
    textAlign: 'center',
    color: tokens.color.ink40,
    paddingRight: 18,
  },

  rowSkipped: { opacity: 0.5 },
  occurrenceChip: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    padding: '6px 10px',
    borderRadius: tokens.radius.control,
    background: tokens.color.surface,
    border: `1px solid ${tokens.color.line}`,
    fontSize: tokens.font.size.sm,
  },
  skippedLabel: {
    fontSize: tokens.font.size.xs,
    color: tokens.color.ink40,
    fontWeight: tokens.font.weight.medium,
  },

  dialogField: { marginTop: 10, width: '100%' },

  dateTimeRow: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: 10,
    marginTop: 22,
  },
  field: {
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    flex: 1,
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
  rangeError: {
    flexBasis: '100%',
    fontSize: 11,
    fontWeight: 600,
    color: tokens.color.fail,
  },

  /**
   * The date picker's own month/year quick-jump popups.
   *
   * A top-level class, not nested inside `datePickerPaper`: this popup is
   * portalled to the document root, so it is never a DOM descendant of the
   * calendar's paper.
   */
  datePickerMenu: {
    minWidth: 220,
    maxHeight: 320,
    padding: 10,
    border: `1px solid ${tokens.color.lineStrong}`,
    borderRadius: tokens.radius.control,
    boxShadow: tokens.shadow.md,
    backgroundColor: tokens.color.surface,

    '& .schedule-date-picker-month-grid, & .schedule-date-picker-year-list': {
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

  datePickerPaper: {
    overflow: 'hidden',
    border: `1px solid ${tokens.color.lineStrong}`,
    borderRadius: tokens.radius.card,
    boxShadow: tokens.shadow.md,
    '& .schedule-date-picker-header': {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '8px 12px 4px',
    },
    '& .schedule-date-picker-heading': {
      display: 'flex',
      alignItems: 'center',
      gap: 4,
    },
    '& .schedule-date-picker-heading button': {
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

  /** The time picker's hour/minute list popup — same visual language as the
   * date calendar's day cells, applied to its scrollable digital-clock columns. */
  timePickerPaper: {
    overflow: 'hidden',
    border: `1px solid ${tokens.color.lineStrong}`,
    borderRadius: tokens.radius.card,
    boxShadow: tokens.shadow.md,
    '& .MuiMultiSectionDigitalClockSection-item, & .MuiDigitalClock-item': {
      fontSize: 13,
      '&.Mui-selected': {
        backgroundColor: tokens.color.running,
        color: tokens.color.surface,
        '&:hover, &:focus': { backgroundColor: tokens.color.running },
      },
      '&:hover': { backgroundColor: tokens.color.runningBg },
    },
  },
}));
