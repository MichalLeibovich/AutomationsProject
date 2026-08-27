import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

export const useStyles = makeStyles()(() => ({
  stack: {
    position: 'fixed',
    insetInline: 0,
    bottom: 28,
    zIndex: tokens.zIndex.toast,
    display: 'flex',
    flexDirection: 'column-reverse',
    alignItems: 'center',
    gap: 8,
    pointerEvents: 'none',
  },
  toast: {
    display: 'flex',
    alignItems: 'center',
    gap: 9,
    padding: '11px 18px',
    borderRadius: tokens.radius.pill,
    background: 'rgba(10,36,78,.94)',
    backdropFilter: 'blur(10px)',
    color: '#fff',
    fontSize: tokens.font.size.base,
    fontWeight: tokens.font.weight.medium,
    boxShadow: tokens.shadow.lg,
    pointerEvents: 'auto',
  },
  icon: {
    display: 'flex',
    fontSize: 17,
  },
}));
