/**
 * Route paths as constants. Navigation calls reference these rather than
 * literals, so a URL change is a single edit.
 *
 * There is no login route: the application has no accounts, so the root
 * redirects straight to the test grid.
 */
export const paths = {
  root: '/',
  tests: '/tests',
  dashboard: '/dashboard',
  timeline: '/timeline',
  calendar: '/calendar',
  notFound: '*',
} as const;

export type AppPath = (typeof paths)[keyof typeof paths];
