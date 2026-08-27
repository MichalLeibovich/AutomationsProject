import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

export const useStyles = makeStyles<{ emphasised: boolean }>()((_theme, { emphasised }) => ({
  root: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
    gap: 11,
    padding: '10px 12px',
    borderRadius: tokens.radius.control,
    background: emphasised ? tokens.color.tintSoft : 'transparent',
    transition: 'background .2s',
    '&:hover': {
      background: emphasised ? tokens.color.tintSoft : 'rgba(10,36,78,.035)',
    },
  },
  main: {
    flex: 1,
    minWidth: 0,
  },
  name: {
    fontSize: 13.5,
    fontWeight: tokens.font.weight.medium,
    letterSpacing: '-.012em',
  },
  meta: {
    fontSize: tokens.font.size.xs,
    color: tokens.color.ink40,
  },
  warning: {
    display: 'flex',
    color: tokens.color.fail,
    flexShrink: 0,
    fontSize: 16,
  },
}));
