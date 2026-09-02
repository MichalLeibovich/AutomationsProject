import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

interface StyleParams {
  color: string;
  wide: boolean;
}

export const useStyles = makeStyles<StyleParams>()((theme, { color, wide }) => ({
  root: {
    position: 'relative',
    overflow: 'hidden',
    padding: '16px 18px 14px',
    borderRadius: tokens.radius.card,
    background: tokens.color.surface,
    border: '1px solid rgba(10,36,78,.05)',
    boxShadow: tokens.shadow.sm,
    transition: `box-shadow .3s ${tokens.ease}, transform .3s ${tokens.ease}`,
    '&:hover': { boxShadow: tokens.shadow.md, transform: 'translateY(-2px)' },

    // Identity bar on the inline start — the right edge under RTL.
    '&::before': {
      content: '""',
      position: 'absolute',
      insetInlineStart: 0,
      top: 0,
      bottom: 0,
      width: 3,
      background: color,
    },
  },

  header: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    marginBottom: 13,
  },

  headerText: { flex: 1, minWidth: 0 },

  headerSearchField: { flexShrink: 0, width: 350 },

  title: {
    fontSize: tokens.font.size.md,
    fontWeight: tokens.font.weight.semibold,
    letterSpacing: '-.015em',
    margin: 0,
  },

  subtitle: {
    fontSize: tokens.font.size.sm,
    color: tokens.color.ink40,
  },

  disclosure: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
    padding: '9px 12px',
    borderRadius: tokens.radius.control,
    fontSize: tokens.font.size.sm,
    fontWeight: tokens.font.weight.medium,
    color: tokens.color.ink60,
    transition: 'background .2s, color .2s',
    '&:hover': { background: 'rgba(10,36,78,.04)', color: tokens.color.ink },
  },

  chevron: {
    display: 'flex',
    fontSize: 18,
    transition: `transform .3s ${tokens.ease}`,
  },

  chevronOpen: { transform: 'rotate(180deg)' },

  /**
   * At full width the secondary list uses two sub-columns instead of one long
   * strip. `align-items: start` prevents a tall child stretching its row
   * siblings — the layout bug that once looked like shared expand state.
   */
  secondaryList: {
    display: wide ? 'grid' : 'flex',
    ...(wide
      ? {
          gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))',
          alignItems: 'start',
          gap: 6,
          [theme.breakpoints.down('lg')]: { gridTemplateColumns: '1fr' },
        }
      : { flexDirection: 'column' as const, gap: 4 }),
    paddingTop: 8,
  },

  fullSpan: { gridColumn: '1 / -1' },

  searchField: { maxWidth: 400 },

  emptyNote: {
    gridColumn: '1 / -1',
    padding: '14px 12px',
    fontSize: tokens.font.size.sm,
    color: tokens.color.ink40,
  },

  count: { color: tokens.color.ink25 },
}));
