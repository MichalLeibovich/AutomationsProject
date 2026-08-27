import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

export const useStyles = makeStyles()(() => ({
  eyebrow: {
    fontSize: tokens.font.size.xs,
    fontWeight: 640,
    color: tokens.color.ink40,
  },
  title: {
    marginTop: 3,
    fontSize: tokens.font.size.lg,
    fontWeight: tokens.font.weight.bold,
    letterSpacing: '-.022em',
  },
  summary: {
    marginTop: 2,
    fontSize: tokens.font.size.sm,
    color: tokens.color.ink40,
  },

  list: {
    display: 'flex',
    flexDirection: 'column',
    gap: 14,
  },

  /** The hour rail sits on the inline start — the right under RTL. */
  hourGroup: {
    display: 'grid',
    gridTemplateColumns: '52px 1fr',
    gap: 12,
  },
  hourLabel: {
    paddingTop: 11,
    fontSize: tokens.font.size.xs,
    fontWeight: 600,
    color: tokens.color.ink40,
  },
  runs: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  run: {
    display: 'flex',
    alignItems: 'center',
    gap: 11,
    width: '100%',
    padding: '10px 12px',
    borderRadius: tokens.radius.control,
    textAlign: 'start',
    transition: 'background .2s',
    '&:hover': { background: 'rgba(10,36,78,.035)' },
  },
  runText: { flex: 1, minWidth: 0 },
  runName: {
    fontSize: 13.5,
    fontWeight: tokens.font.weight.medium,
  },
  runMeta: {
    fontSize: tokens.font.size.xs,
    color: tokens.color.ink40,
  },
  chevron: {
    display: 'flex',
    fontSize: 17,
    color: tokens.color.ink25,
  },
}));
