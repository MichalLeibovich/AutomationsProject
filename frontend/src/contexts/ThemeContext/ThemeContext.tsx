import { useMemo } from 'react';
import type { PropsWithChildren } from 'react';
import { CacheProvider } from '@emotion/react';
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import type { Theme } from '@mui/material';
import { TssCacheProvider } from 'tss-react';
import { tokens } from '@/theme/tokens';
import { muiCache, tssCache } from './rtlCache';

/**
 * Builds the MUI theme from the design tokens. Exported separately so tests
 * can render components without the full provider tree.
 */
export const buildTheme = (): Theme =>
  createTheme({
    direction: 'rtl',
    palette: {
      mode: 'light',
      primary: { main: tokens.color.ink, contrastText: '#FFFFFF' },
      secondary: { main: tokens.color.tint, contrastText: tokens.color.ink },
      success: { main: tokens.color.pass, light: tokens.color.passBg },
      error: { main: tokens.color.fail, light: tokens.color.failBg },
      info: { main: tokens.color.running, light: tokens.color.runningBg },
      background: { default: tokens.color.canvas, paper: tokens.color.surface },
      text: {
        primary: tokens.color.ink,
        secondary: tokens.color.ink60,
        disabled: tokens.color.ink25,
      },
      divider: tokens.color.line,
    },
    shape: { borderRadius: tokens.radius.control },
    spacing: 4,
    typography: {
      fontFamily: tokens.font.family,
      fontSize: tokens.font.size.md,
      // Hebrew glyphs have no case, so uppercase transforms and wide tracking
      // are disabled globally rather than overridden per component.
      button: { textTransform: 'none', fontWeight: tokens.font.weight.semibold },
      h1: {
        fontSize: tokens.font.size.xl,
        fontWeight: tokens.font.weight.bold,
        letterSpacing: '-.03em',
      },
      h2: {
        fontSize: tokens.font.size.lg,
        fontWeight: tokens.font.weight.bold,
        letterSpacing: '-.022em',
      },
      h3: {
        fontSize: tokens.font.size.md,
        fontWeight: tokens.font.weight.semibold,
        letterSpacing: '-.015em',
      },
      body1: { fontSize: tokens.font.size.md },
      body2: { fontSize: tokens.font.size.base },
      caption: { fontSize: tokens.font.size.xs },
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            backgroundColor: tokens.color.canvas,
            WebkitFontSmoothing: 'antialiased',
          },
          // Tabular figures so live timers tick without shifting the layout.
          // `isolate` stops digits reordering against adjacent Hebrew text.
          '.num': {
            fontVariantNumeric: 'tabular-nums lining-nums',
            fontFeatureSettings: "'tnum' 1",
            unicodeBidi: 'isolate',
          },
          '@media (prefers-reduced-motion: reduce)': {
            '*': {
              animationDuration: '.01ms !important',
              transitionDuration: '.01ms !important',
            },
          },
        },
      },
      MuiButtonBase: { defaultProps: { disableRipple: true } },
      MuiPaper: { defaultProps: { elevation: 0 } },
      MuiTooltip: { defaultProps: { arrow: true, enterDelay: 400 } },
    },
  });

/**
 * Provides the RTL emotion caches and the MUI theme.
 *
 * Deliberately a Context provider rather than a Jotai atom: the value is
 * tree-scoped, never mutated by application logic, and is read through MUI's
 * own `useTheme`, so an atom would add indirection without adding anything.
 */
export function AppThemeProvider({ children }: PropsWithChildren) {
  const theme = useMemo(buildTheme, []);

  return (
    <CacheProvider value={muiCache}>
      <TssCacheProvider value={tssCache}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          {children}
        </ThemeProvider>
      </TssCacheProvider>
    </CacheProvider>
  );
}
