import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { Provider as JotaiProvider } from 'jotai';
import { AppThemeProvider } from '@/contexts/ThemeContext/ThemeContext';
import { ConfirmProvider } from '@/contexts/ConfirmContext/ConfirmContext';
import { ToastHost } from '@/components/ToastHost/ToastHost';
import { AppRoutes } from '@/routes/AppRoutes';

/**
 * Application entry point.
 *
 * Provider order matters: the theme provider installs the right-to-left emotion
 * caches, so it wraps everything that renders MUI components. ToastHost sits
 * outside the router because a notification should survive navigation.
 *
 * There is no session bootstrap — the application has no accounts, so the first
 * paint needs no round trip and the grid renders immediately.
 */
const container = document.getElementById('root');
if (!container) throw new Error('Root element #root not found');

createRoot(container).render(
  <StrictMode>
    <JotaiProvider>
      <AppThemeProvider>
        <ConfirmProvider>
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
          <ToastHost />
        </ConfirmProvider>
      </AppThemeProvider>
    </JotaiProvider>
  </StrictMode>,
);
