import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

export const useStyles = makeStyles()(() => ({
  root: {
    padding: '16px 18px',
    borderRadius: tokens.radius.card,
    background: tokens.color.surface,
    border: '1px solid rgba(10,36,78,.05)',
    boxShadow: tokens.shadow.sm,
  },
  label: {
    fontSize: tokens.font.size.xs,
    fontWeight: 640,
    color: tokens.color.ink40,
  },
  value: {
    margin: '8px 0 3px',
    fontSize: tokens.font.size.xl,
    fontWeight: tokens.font.weight.bold,
    letterSpacing: '-.035em',
    lineHeight: 1.1,
  },
  hint: {
    fontSize: tokens.font.size.sm,
    color: tokens.color.ink40,
  },
}));
