import type { Application } from '@/types/application.types';
import { GENERAL_COLOR, GENERAL_SCOPE } from './constants';

/** `null` = all applications (excluding General). A name = that application. */
export type ScopeSelection = string | null;

export const isGeneralScope = (scope: ScopeSelection): boolean => scope === GENERAL_SCOPE;

/**
 * Resolves an identity colour from either an application id or a scope label.
 * Runs carry a label rather than an id, so both are accepted.
 */
export const resolveScopeColor = (
  applications: Application[],
  identifier: string | null,
): string => {
  if (identifier === GENERAL_SCOPE) return GENERAL_COLOR;
  const match = applications.find(
    (application) => application.id === identifier || application.name === identifier,
  );
  return match?.color ?? '#8A96AC';
};

/** Applications visible for the current scope selection. */
export const visibleApplications = (
  applications: Application[],
  scope: ScopeSelection,
): Application[] => {
  if (scope === null) return applications;
  if (scope === GENERAL_SCOPE) return [];
  return applications.filter((application) => application.name === scope);
};
