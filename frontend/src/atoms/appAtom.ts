import { atom } from 'jotai';
import type { Application } from '@/types/application.types';
import type { ScopeSelection } from '@/utils/scope';
import { GENERAL_SCOPE } from '@/utils/constants';
import { visibleApplications } from '@/utils/scope';

export const VIEWS = ['tests', 'dashboard', 'timeline', 'calendar', 'scheduled'] as const;
export type ViewId = (typeof VIEWS)[number];

/** Mirrors the URL. The router is the source of truth; this is the read model. */
export const activeViewAtom = atom<ViewId>('tests');

/** The calendar and scheduled-automations views are deliberately all-scopes,
 * so the filter row is hidden there. */
export const scopeFilterVisibleAtom = atom(
  (get) => !['calendar', 'scheduled'].includes(get(activeViewAtom)),
);

export const applicationsAtom = atom<Application[]>([]);

/** `null` = all applications (excluding General). */
export const selectedScopeAtom = atom<ScopeSelection>(null);

export const isGeneralScopeAtom = atom((get) => get(selectedScopeAtom) === GENERAL_SCOPE);

export const visibleApplicationsAtom = atom<Application[]>((get) =>
  visibleApplications(get(applicationsAtom), get(selectedScopeAtom)),
);

/** Toggle semantics: selecting the active scope returns to "all applications". */
export const toggleScopeAtom = atom(null, (get, set, scope: string) => {
  set(selectedScopeAtom, get(selectedScopeAtom) === scope ? null : scope);
});
