import createCache from '@emotion/cache';
import { prefixer } from 'stylis';
import rtlPlugin from 'stylis-plugin-rtl';

/**
 * Two separate emotion caches, by design.
 *
 * MUI's own styles and tss-react's styles must not share a cache: on equal
 * specificity the rules inserted later win, and component styles need to
 * override MUI defaults. `prepend` puts MUI's cache first.
 *
 * Both caches run the RTL plugin, which flips physical CSS properties
 * (margin-left, padding-right, translateX…) at insertion time. That is why
 * components can be authored as if LTR and still render correctly in Hebrew.
 */
const stylisPlugins = [prefixer, rtlPlugin];

export const muiCache = createCache({
  key: 'mui',
  stylisPlugins,
  prepend: true,
});

export const tssCache = createCache({
  key: 'tss',
  stylisPlugins,
});
