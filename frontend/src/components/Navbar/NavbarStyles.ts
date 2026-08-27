import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

export const useStyles = makeStyles()((theme) => ({
  root: {
    position: 'sticky',
    top: 0,
    zIndex: tokens.zIndex.header,
    background: 'rgba(255,255,255,.78)',
    backdropFilter: 'saturate(180%) blur(20px)',
    borderBottom: `1px solid ${tokens.color.line}`,
  },

  inner: {
    maxWidth: 1440,
    margin: '0 auto',
    padding: '14px 24px 0',
    [theme.breakpoints.down('md')]: { padding: '12px 14px 0' },
  },

  row: {
    display: 'flex',
    alignItems: 'center',
    gap: 20,
    [theme.breakpoints.down('md')]: { flexWrap: 'wrap', gap: 12 },
  },

  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: 11,
    flexShrink: 0,
  },

  mark: {
    display: 'grid',
    placeItems: 'center',
    width: 38,
    height: 38,
    borderRadius: 11,
    background: `linear-gradient(150deg, #12386f, ${tokens.color.ink})`,
    boxShadow: tokens.shadow.sm,
    color: '#fff',
    fontSize: 9,
    fontWeight: 700,
    // Retained only on the Latin wordmark; Hebrew never gets letter-spacing.
    letterSpacing: '.09em',
  },

  wordmark: {
    fontSize: 16,
    fontWeight: tokens.font.weight.bold,
    letterSpacing: '-.022em',
    lineHeight: 1.1,
  },

  tagline: {
    fontSize: tokens.font.size.xs,
    color: tokens.color.ink40,
  },

  spacer: { flex: 1 },

  spacerRow: { height: 13 },

  user: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    flexShrink: 0,
  },

  avatar: {
    width: 30,
    height: 30,
    fontSize: 11.5,
    fontWeight: tokens.font.weight.semibold,
    background: tokens.color.tint,
    color: tokens.color.ink,
  },
}));
