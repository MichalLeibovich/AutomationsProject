import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

export const useStyles = makeStyles()(() => ({
  paper: {
    borderRadius: tokens.radius.card,
    padding: 4,
    maxWidth: 420,
  },
  title: {
    fontSize: tokens.font.size.lg,
    fontWeight: tokens.font.weight.bold,
    letterSpacing: '-.022em',
    paddingBottom: 6,
  },
  body: {
    fontSize: tokens.font.size.base,
    color: tokens.color.ink60,
  },
  actions: {
    padding: '10px 20px 16px',
    gap: 8,
  },
}));
