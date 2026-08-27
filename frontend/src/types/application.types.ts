/** Application and automation types. */

/** A monitored application. */
export interface Application {
  id: string;
  /** Display name, also used as the scope identifier in the filter row. */
  name: string;
  /** Stable URL-safe identifier. */
  slug: string;
  /** Identity colour as `#RRGGBB`, consistent across every view. */
  color: string;
  /** Sort position in the filter row and grid. */
  displayOrder: number;
  isActive: boolean;
}

/**
 * Which automations a scope covers.
 *
 * The two are disjoint: general automation belongs to no product, so an
 * all-applications view excludes it.
 */
export type TestScope = 'application' | 'general';

/**
 * An automation's role within its card.
 *
 * `main` is the one an operator runs by reflex, so each application has exactly
 * one and it leads the card. General automations have no hierarchy among them.
 */
export type TestKind = 'main' | 'secondary' | 'general';

/** A runnable automation. */
export interface TestDefinition {
  id: string;
  /** Owning application. Null for general automation. */
  applicationId: string | null;
  /** Owning application's name, joined by the API for display. */
  applicationName: string | null;
  scope: TestScope;
  kind: TestKind;
  name: string;
  description: string | null;
  /**
   * The pytest node id the runner executes, for example
   * `tests/magen-elyon/test_login.py::test_valid_login`.
   *
   * This is what ties a catalog entry to an actual automation on disk, and is
   * how the suite reports results back against the right definition.
   */
  runnerTarget: string;
  displayOrder: number;
  /** Runner timeout, after which the run is marked timed out. */
  timeoutSeconds: number;
  isActive: boolean;
}

/**
 * The active scope selection.
 *
 * Null means all applications and deliberately excludes general automation;
 * `'general'` selects general automation alone; any other string is an
 * application name.
 */
export type ScopeSelection = string | null;
