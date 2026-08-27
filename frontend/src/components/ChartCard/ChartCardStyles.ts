import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

export const useStyles = makeStyles<{ height: number }>()((_theme, { height }) => ({
  root: {
    padding: '18px 20px 8px',
    borderRadius: tokens.radius.card,
    background: tokens.color.surface,
    border: '1px solid rgba(10,36,78,.05)',
    boxShadow: tokens.shadow.sm,
  },
  header: { marginBottom: 14 },
  title: {
    fontSize: tokens.font.size.md,
    fontWeight: tokens.font.weight.semibold,
    letterSpacing: '-.015em',
  },
  subtitle: {
    fontSize: tokens.font.size.sm,
    color: tokens.color.ink40,
  },
  body: { height },
}));
