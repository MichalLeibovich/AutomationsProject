import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

export const useStyles = makeStyles()(() => ({
  granted: { color: tokens.color.pass },
  denied: { color: tokens.color.ink25 },
}));
