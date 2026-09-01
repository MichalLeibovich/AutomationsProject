/**
 * Design tokens — the single source of truth for the visual language.
 * Consumed by the MUI theme and by every useStyles hook. No component
 * may hardcode a colour, radius, shadow or easing curve.
 */
export const tokens = {
  color: {
    ink: '#0A244E',
    ink80: '#33496E',
    ink60: '#5C6E8C',
    ink40: '#8896AB',
    ink25: '#B3BDCC',

    tint: '#D3E3FD',
    tintSoft: '#E7EEFC',
    tintDeep: '#B9D3FB',

    canvas: '#EDF2FA',
    surface: '#FFFFFF',

    // focusedComment: '#dfe1e4',

    line: 'rgba(10,36,78,.09)',
    lineStrong: 'rgba(10,36,78,.16)',

    pass: '#0E9F6E',
    passBg: '#E4F6EE',
    fail: '#E0334B',
    failBg: '#FDEAEE',
    running: '#2F6BFF',
    runningBg: '#E7EFFF',
    idle: '#8A96AC',
    idleBg: '#EDF1F7',

    generalScope: '#6B7A94',
  },

  radius: {
    card: 20,
    control: 12,
    sm: 9,
    pill: 999,
    panel: 24,
  },

  shadow: {
    sm: '0 1px 2px rgba(10,36,78,.05), 0 1px 3px rgba(10,36,78,.04)',
    md: '0 2px 6px rgba(10,36,78,.05), 0 14px 30px -10px rgba(10,36,78,.12)',
    lg: '0 32px 70px -16px rgba(10,36,78,.32), 0 2px 8px rgba(10,36,78,.10)',
    panel: '34px 0 74px -22px rgba(10,36,78,.34)',
    sheet: '0 -26px 64px -18px rgba(10,36,78,.36)',
  },

  font: {
    family:
      '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", Assistant, Heebo, "Arial Hebrew", "Segoe UI", system-ui, sans-serif',
    size: { xs: 11.5, sm: 12.5, base: 13, md: 14.5, lg: 17, xl: 23 },
    weight: { regular: 450, medium: 550, semibold: 620, bold: 660 },
  },

  ease: 'cubic-bezier(.32,.72,0,1)',

  zIndex: {
    header: 40,
    scrim: 1200,
    panel: 1201,
    toast: 1400,
  },

  /** Chart colours, keyed so a given failure cause looks identical everywhere. */
  chartPalette: ['#EF4444', '#F97316', '#F59E0B', '#6366F1', '#14B8A6', '#8B5CF6'],
} as const;

export type Tokens = typeof tokens;
