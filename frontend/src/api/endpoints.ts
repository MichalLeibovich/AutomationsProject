/**
 * Every API path, in one place.
 *
 * Services compose from these constants, so a route change is a single edit and
 * no path string is written twice. Parameterised paths are functions rather than
 * template literals at the call site, which keeps interpolation consistent.
 */
export const endpoints = {
  applications: {
    list: '/applications',
    create: '/applications',
    /** @param applicationId - The application's identifier. */
    byId: (applicationId: string) => `/applications/${applicationId}`,
  },

  testDefinitions: {
    list: '/test-definitions',
    create: '/test-definitions',
    /** @param definitionId - The definition's identifier. */
    byId: (definitionId: string) => `/test-definitions/${definitionId}`,
    /** Resolve an automation by its pytest node id. */
    byTarget: '/test-definitions/by-target',
  },

  runs: {
    list: '/runs',
    create: '/runs',
    bulk: '/runs/bulk',
    /** Direct CSV download; the API streams it rather than queueing a job. */
    export: '/runs/export',
    /** Server-sent event stream of live run status. */
    stream: '/runs/stream',
    /** @param runId - The run's identifier. */
    byId: (runId: string) => `/runs/${runId}`,
    /** @param runId - The run to cancel. */
    cancel: (runId: string) => `/runs/${runId}/cancel`,
    /** @param runId - The run whose per-step detail to read. */
    steps: (runId: string) => `/runs/${runId}/steps`,
    /** @param runId - The run whose artifacts to list. */
    artifacts: (runId: string) => `/runs/${runId}/artifacts`,
    /** @param runId - The run whose comments to read or add to. */
    comments: (runId: string) => `/runs/${runId}/comments`,
    /**
     * @param runId - The run the comment belongs to.
     * @param commentId - The comment to remove.
     */
    comment: (runId: string, commentId: string) => `/runs/${runId}/comments/${commentId}`,
  },

  analytics: {
    dashboard: '/analytics/dashboard',
    calendar: '/analytics/calendar',
  },
} as const;
