import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

export const useStyles = makeStyles()((theme) => ({
  root: {
    minHeight: '100vh',
    background: tokens.color.canvas,
    color: tokens.color.ink,
  },
  main: {
    maxWidth: 1440,
    margin: '0 auto',
    padding: '22px 24px 64px',
    [theme.breakpoints.down('md')]: { padding: '18px 14px 48px' },
  },
}));
