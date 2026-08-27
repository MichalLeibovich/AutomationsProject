import { keyframes } from 'tss-react';
import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

const stepIn = keyframes`
  from { opacity: 0; transform: translateX(-15px); }
  to   { opacity: 1; transform: none; }
`;

export const useStyles = makeStyles()((theme) => ({
  /**
   * Anchored top-to-bottom so content of any length scrolls rather than
   * clipping — the failure mode a centred dialog has by construction.
   */
  paper: {
    width: 'min(580px, 100%)',
    display: 'flex',
    flexDirection: 'column',
    background: tokens.color.surface,
    borderInlineStart: `1px solid ${tokens.color.line}`,
    boxShadow: tokens.shadow.panel,
    backgroundImage: 'none',

    [theme.breakpoints.down('sm')]: {
      width: '100%',
      height: 'min(90vh, 100%)',
      borderInlineStart: 0,
      borderTop: `1px solid ${tokens.color.line}`,
      borderRadius: `${tokens.radius.panel}px ${tokens.radius.panel}px 0 0`,
      boxShadow: tokens.shadow.sheet,
    },
  },

  /** Grab handle, shown only in the mobile bottom-sheet presentation. */
  handle: {
    display: 'none',
    [theme.breakpoints.down('sm')]: {
      display: 'block',
      position: 'absolute',
      top: 9,
      left: '50%',
      marginLeft: -19,
      width: 38,
      height: 4,
      borderRadius: 2,
      background: tokens.color.lineStrong,
    },
  },

  header: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: 11,
    flexShrink: 0,
    padding: '17px 17px 14px',
    borderBottom: `1px solid ${tokens.color.line}`,
    [theme.breakpoints.down('sm')]: { paddingTop: 22 },
  },

  headerContent: { flex: 1, minWidth: 0 },

  /**
   * Scroll-edge shadows appear only where content continues, so a long
   * debrief reads as scrollable rather than truncated.
   */
  body: {
    flex: 1,
    minHeight: 0,
    overflowY: 'auto',
    padding: '18px 17px 24px',
    background: [
      `linear-gradient(${tokens.color.surface} 34%, rgba(255,255,255,0)) top / 100% 26px no-repeat local`,
      `linear-gradient(rgba(255,255,255,0), ${tokens.color.surface} 66%) bottom / 100% 26px no-repeat local`,
      'radial-gradient(farthest-side at 50% 0, rgba(10,36,78,.11), rgba(10,36,78,0)) top / 100% 11px no-repeat scroll',
      'radial-gradient(farthest-side at 50% 100%, rgba(10,36,78,.11), rgba(10,36,78,0)) bottom / 100% 11px no-repeat scroll',
    ].join(', '),
  },

  step: {
    animation: `${stepIn} .3s ${tokens.ease} both`,
  },

  footer: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: 8,
    flexShrink: 0,
    padding: '13px 17px',
    borderTop: `1px solid ${tokens.color.line}`,
    background: 'rgba(237,242,250,.55)',
  },

  crumb: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 4,
    marginBottom: 5,
    paddingBlock: 3,
    paddingInlineStart: 4,
    paddingInlineEnd: 8,
    borderRadius: tokens.radius.pill,
    fontSize: 12,
    fontWeight: tokens.font.weight.semibold,
    color: tokens.color.ink40,
    transition: 'all .18s',
    '&:hover': { background: tokens.color.tintSoft, color: tokens.color.ink },
  },

  crumbIcon: { display: 'flex', fontSize: 16 },
}));
