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

  overview: {
    // Deliberately unboxed — the three panels below are the only bordered
    // shapes in this section, so the "row" reads as alignment, not a table.
  },
  overviewRow: {
    display: 'flex',
    alignItems: 'stretch',
    gap: 14,
  },
  nameColumn: {
    display: 'flex',
    flexDirection: 'column',
    minWidth: 140,
    // Mirrors `panel`'s top/bottom padding so the name column's rows fall at
    // the exact same y as the panels' rows instead of sitting higher.
    padding: '10px 6px 6px 0',
  },
  nameRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    minHeight: 48,
    fontWeight: tokens.font.weight.semibold,
    fontSize: tokens.font.size.md,
  },
  nameText: {
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },

  panel: {
    flex: 1,
    minWidth: 0,
    borderRadius: tokens.radius.card,
    background: tokens.color.surface,
    border: '1px solid rgba(10,36,78,.05)',
    boxShadow: tokens.shadow.sm,
    padding: '10px 16px 6px',
  },
  panelHeading: {
    minHeight: 48,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    textAlign: 'center',
    marginBottom: 4,
  },
  panelHeadingBig: {
    fontSize: tokens.font.size.lg,
    fontWeight: tokens.font.weight.semibold,
    lineHeight: 1.2,
  },
  panelHeadingSmall: {
    fontSize: tokens.font.size.sm,
    color: tokens.color.ink40,
    fontWeight: tokens.font.weight.medium,
  },
  panelRow: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 2,
    minHeight: 48,
    textAlign: 'center',
  },
  panelRowValue: {
    fontSize: tokens.font.size.md,
    fontWeight: tokens.font.weight.semibold,
    color: tokens.color.ink,
  },
  panelRowMuted: {
    fontSize: tokens.font.size.sm,
    color: tokens.color.ink40,
  },
  panelRowTag: {
    fontSize: tokens.font.size.sm,
    color: tokens.color.ink40,
    fontWeight: tokens.font.weight.medium,
  },

  groupList: {
    display: 'flex',
    flexDirection: 'column',
    overflowY: "auto",
    gap: 10,
    height: "300px",
    direction: "rtl",

    // Scrollbar
    scrollbarWidth: 'thin',
    scrollbarColor: `${tokens.color.ink25} transparent`,

    '&::-webkit-scrollbar': {
      width: 8,
    },
    paddingLeft: 5, // space between content and scrollbar
  },
  group: {
    display: 'flex',
    direction: "ltr",
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
