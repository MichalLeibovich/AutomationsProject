import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

export const useStyles = makeStyles()(() => ({
  eyebrow: {
    fontSize: tokens.font.size.xs,
    fontWeight: 640,
    color: tokens.color.ink40,
  },
  titleRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    marginTop: 3,
    flexWrap: 'wrap',
  },
  title: {
    fontSize: tokens.font.size.lg,
    fontWeight: tokens.font.weight.bold,
    letterSpacing: '-.022em',
  },
  subtitle: {
    marginTop: 2,
    fontSize: tokens.font.size.sm,
    color: tokens.color.ink40,
  },

  root: {
    display: 'flex',
    flexDirection: 'column',
    gap: 18,
  },

  /** 1px gap plus a tinted parent renders hairline dividers without borders. */
  metaGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
    gap: 1,
    borderRadius: tokens.radius.control,
    overflow: 'hidden',
    textAlign: "center",
    // background: tokens.color.line,
    // backgroundColor: "red",
  },
  metaCell: {
    background: tokens.color.surface,
    padding: '11px 13px',
    // backgroundColor: "black"
  },
  metaLabel: {
    fontSize: tokens.font.size.xs,
    fontWeight: 640,
    marginBottom: 3,
    color: tokens.color.ink40,
  },
  metaValue: {
    fontWeight: tokens.font.weight.semibold,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    direction: 'rtl',
  },

  idValue: {
    display: 'flex',
    alignItems: 'center',
    gap: 4,

  },

  sectionTitle: {
    marginBottom: 8,
    fontSize: tokens.font.size.md,
    fontWeight: tokens.font.weight.semibold,
  },

  callout: {
    display: 'flex',
    gap: 11,
    padding: '13px 15px',
    borderRadius: tokens.radius.control,
    background: tokens.color.failBg,
    color: '#8e1d2f',
    fontSize: tokens.font.size.base,
  },
  calloutIcon: { display: 'flex', fontSize: 19, flexShrink: 0, marginTop: 1 },
  calloutHeading: { marginBottom: 2, fontWeight: 620 },

  shotGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 10,
  },
  shot: {
    display: 'grid',
    placeItems: 'center',
    aspectRatio: '16 / 10',
    borderRadius: 10,
    background: tokens.color.tintSoft,
    boxShadow: `inset 0 0 0 1px ${tokens.color.line}`,
    color: tokens.color.ink25,
    overflow: 'hidden',
    '& img': { width: '100%', height: '100%', objectFit: 'cover' },
  },

  thread: {
    display: 'flex',
    flexDirection: 'column',
    gap: 13,
    marginBottom: 14,
  },
  comment: { display: 'flex', gap: 10 },
  avatar: {
    width: 29,
    height: 29,
    fontSize: 11,
    fontWeight: 640,
    background: tokens.color.tint,
    color: tokens.color.ink,
  },
  commentBody: { flex: 1 },
  commentHead: {
    display: 'flex',
    gap: 7,
    alignItems: 'baseline',
  },
  commentAuthor: {
    fontWeight: 620,
    fontSize: tokens.font.size.base,
  },
  commentTime: {
    fontSize: tokens.font.size.xs,
    color: tokens.color.ink40,
  },
  commentText: {
    marginTop: 2,
    fontSize: tokens.font.size.base,
    overflowWrap: 'anywhere',
    whiteSpace: 'pre-wrap',
  },

  authorInput: {

    marginBlockEnd: 8,

  },

  composerRow: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 10,
    width: '100%',
  },

  composer: { display: 'flex', gap: 8 },
  composerInput: {
    width: '95%',

    '& .MuiOutlinedInput-root': {
      borderRadius: tokens.radius.control,
      background: tokens.color.tintSoft,
      height: '80px',
      fontSize: tokens.font.size.base,

      '& .MuiInputBase-inputMultiline': {
        height: '100% !important',
        boxSizing: 'border-box',
        textAlign: 'start',
      },

      '& fieldset': {
        border: 0,
      },

      '&.Mui-focused': {
        boxShadow: `inset 0 0 0 1.5px ${tokens.color.running}`,
      },
    },
  },

  emptyNote: {
    marginBottom: 12,
    fontSize: tokens.font.size.sm,
    color: tokens.color.ink40,
  },
}));
