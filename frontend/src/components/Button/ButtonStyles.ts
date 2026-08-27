import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

/**
 * All Button appearance lives here. The component file contains no styling
 * logic — it only chooses which class names to apply.
 */
export const useStyles = makeStyles()(() => ({
  root: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 0,
    fontWeight: tokens.font.weight.semibold,
    letterSpacing: '-.01em',
    whiteSpace: 'nowrap',
    transition: `transform .16s ${tokens.ease}, background .18s, box-shadow .18s, opacity .18s`,
    '&:active:not(:disabled)': { transform: 'scale(.97)' },
    '&.Mui-disabled': { opacity: 0.4 },
  },

  // ---- variants ----
  primary: {
    background: tokens.color.ink,
    color: '#fff',
    boxShadow: '0 1px 2px rgba(10,36,78,.2), 0 6px 16px -6px rgba(10,36,78,.5)',
    '&:hover': { background: '#123566' },
  },
  tint: {
    background: tokens.color.tint,
    color: tokens.color.ink,
    '&:hover': { background: tokens.color.tintDeep },
  },
  ghost: {
    background: 'transparent',
    color: tokens.color.ink60,
    '&:hover': { background: 'rgba(10,36,78,.055)', color: tokens.color.ink },
  },
  danger: {
    background: tokens.color.failBg,
    color: tokens.color.fail,
    '&:hover': { background: '#fbdde3' },
  },

  // ---- sizes ----
  medium: {
    padding: '9px 16px',
    fontSize: tokens.font.size.base,
    borderRadius: tokens.radius.control,
    gap: 7,
  },
  small: {
    padding: '6px 12px',
    fontSize: tokens.font.size.sm,
    borderRadius: tokens.radius.sm,
    gap: 5,
  },
  icon: {
    padding: 8,
    borderRadius: 10,
    gap: 0,
  },
}));
