import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

export const useStyles = makeStyles()(() => ({
  root: {
    display: 'flex',
    gap: 7,
    padding: '12px 0 13px',
    overflowX: 'auto',
    scrollbarWidth: 'none',
    '&::-webkit-scrollbar': { display: 'none' },
  },

  pill: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 7,
    paddingBlock: 6,
    paddingInlineStart: 10,
    paddingInlineEnd: 13,
    borderRadius: tokens.radius.pill,
    background: tokens.color.surface,
    boxShadow: `inset 0 0 0 1px ${tokens.color.line}`,
    fontSize: tokens.font.size.sm,
    fontWeight: tokens.font.weight.medium,
    color: tokens.color.ink60,
    whiteSpace: 'nowrap',
    transition: `all .2s ${tokens.ease}`,
    '&:hover': {
      color: tokens.color.ink,
      boxShadow: `inset 0 0 0 1px ${tokens.color.lineStrong}`,
    },
  },

  pillActive: {
    background: tokens.color.ink,
    color: '#fff',
    boxShadow: '0 2px 8px -2px rgba(10,36,78,.4)',
    '&:hover': { color: '#fff', background: '#123566' },
  },

  count: {
    fontSize: 11,
    color: tokens.color.ink25,
  },

  countActive: {
    color: 'rgba(255,255,255,.6)',
  },

  /**
   * Hairlines separate the two mode bookends from the application pills,
   * reinforcing that "all apps" and "general" are scopes, not products.
   */
  divider: {
    width: 1,
    flexShrink: 0,
    alignSelf: 'stretch',
    margin: '3px 5px',
    background: tokens.color.lineStrong,
  },

  dot: {
    width: 8,
    height: 8,
    borderRadius: '50%',
    flexShrink: 0,
  },

  icon: {
    display: 'flex',
    fontSize: 14,
  },
}));
