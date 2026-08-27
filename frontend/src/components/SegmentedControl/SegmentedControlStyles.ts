import { makeStyles } from 'tss-react/mui';
import { tokens } from '@/theme/tokens';

interface StyleParams {
  small: boolean;
}

export const useStyles = makeStyles<StyleParams>()((_theme, { small }) => ({
  root: {
    position: 'relative',
    display: 'flex',
    padding: 3,
    borderRadius: tokens.radius.control,
    background: tokens.color.tintSoft,
    boxShadow: 'inset 0 0 0 1px rgba(10,36,78,.05)',
  },

  /**
   * The sliding highlight.
   *
   * Horizontal position and width are set **inline only**, from a measurement of
   * the active option. Nothing horizontal is declared here on purpose: the RTL
   * stylis plugin rewrites `left` to `right`, and an element with `right` from a
   * class plus `left` and `width` inline is over-constrained — under
   * `direction: rtl` the browser keeps `right` and throws the inline `left`
   * away, which pins the highlight to one edge and stops it moving at all.
   *
   * The inline style also sets `right: auto` so any stray rule cannot
   * reintroduce the conflict.
   */
  thumb: {
    position: 'absolute',
    top: 3,
    bottom: 3,
    borderRadius: 9,
    background: tokens.color.surface,
    boxShadow: tokens.shadow.sm,
    // The transition lives inline too: the RTL plugin rewrites `left` to
    // `right` even inside a transition list, which would animate a property
    // nothing sets and make the highlight jump rather than slide.
    pointerEvents: 'none',
  },

  option: {
    position: 'relative',
    zIndex: 1,
    flex: '0 0 auto',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    padding: small ? '6px 13px' : '7px 15px',
    borderRadius: 9,
    fontSize: small ? tokens.font.size.sm : tokens.font.size.base,
    fontWeight: tokens.font.weight.medium,
    letterSpacing: '-.01em',
    color: tokens.color.ink60,
    whiteSpace: 'nowrap',
    transition: 'color .2s',
    '&:hover': { color: tokens.color.ink },
  },

  optionActive: {
    color: tokens.color.ink,
    fontWeight: tokens.font.weight.semibold,
  },

  optionIcon: {
    display: 'flex',
    fontSize: 15,
  },
}));
