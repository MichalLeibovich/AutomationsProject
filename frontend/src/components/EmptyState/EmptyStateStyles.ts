import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

export const useStyles = makeStyles()(() => ({
  root: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 9,
    padding: '52px 24px',
    textAlign: 'center',
  },
  icon: {
    display: 'grid',
    placeItems: 'center',
    width: 44,
    height: 44,
    borderRadius: 14,
    background: tokens.color.tintSoft,
    color: tokens.color.ink25,
    fontSize: 21,
  },
  title: {
    fontSize: tokens.font.size.md,
    fontWeight: tokens.font.weight.semibold,
    letterSpacing: '-.015em',
  },
  body: {
    maxWidth: 340,
    fontSize: tokens.font.size.sm,
    color: tokens.color.ink40,
  },
}));
