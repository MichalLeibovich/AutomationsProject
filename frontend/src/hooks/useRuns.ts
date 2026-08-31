import { useCallback, useEffect, useState } from 'react';
import { ApiError } from '@/api/client';
import { analyticsService } from '@/services/analyticsService';
import { catalogService } from '@/services/catalogService';
import { runService } from '@/services/runService';
import type {
  CalendarDay,
  DashboardParams,
  DashboardResponse,
  RunListParams,
} from '@/types/api.types';
import type { Application, TestDefinition } from '@/types/application.types';
import type { RunComment, TestRun } from '@/types/run.types';

export interface AsyncState<T> {
  data: T | null;
  isLoading: boolean;
  error: ApiError | null;
  reload: () => void;
}

/**
 * Minimal async-state primitive.
 *
 * `deps` is the identity of the request. `fetcher` is intentionally not a
 * dependency: callers usually pass an inline closure, which would change on
 * every render and loop.
 */
export function useAsync<T>(
  fetcher: () => Promise<T>,
  deps: unknown[],
  enabled = true,
): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(enabled);
  const [error, setError] = useState<ApiError | null>(null);
  const [nonce, setNonce] = useState(0);

  const reload = useCallback(() => setNonce((value) => value + 1), []);

  useEffect(() => {
    if (!enabled) {
      setIsLoading(false);
      return;
    }

    let cancelled = false;
    setIsLoading(true);
    setError(null);

    fetcher()
      .then((result) => {
        // Guards against a slow earlier request overwriting a newer result.
        if (!cancelled) setData(result);
      })
      .catch((cause: unknown) => {
        if (!cancelled) {
          setError(cause instanceof ApiError ? cause : new ApiError(0, 'unknown', 'שגיאה', 'unknown'));
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, enabled, nonce]);

  return { data, isLoading, error, reload };
}

export const useApplications = (): AsyncState<Application[]> =>
  useAsync(() => catalogService.listApplications(), []);

export const useTestDefinitions = (scope: string | null): AsyncState<TestDefinition[]> =>
  useAsync(() => catalogService.listTestDefinitions(scope), [scope]);

export const useRunList = (params: RunListParams) =>
  useAsync(
    () => runService.list(params),
    [
      params.scope,
      params.status,
      params.triggerSource,
      params.search,
      params.from,
      params.to,
      params.sort,
      params.direction,
      params.limit,
      params.offset,
    ],
  );

export const useDashboard = (
  params: DashboardParams,
  enabled = true,
): AsyncState<DashboardResponse> =>
  useAsync(
    () => analyticsService.getDashboard(params),
    [params.scope, params.range, params.from, params.to],
    enabled,
  );

export const useCalendarMonth = (year: number, month: number): AsyncState<CalendarDay[]> =>
  useAsync(() => analyticsService.getCalendarMonth(year, month), [year, month]);

export const useRunComments = (runId: string | null): AsyncState<RunComment[]> =>
  useAsync(() => runService.listComments(runId as string), [runId], runId !== null);

export const useDayRuns = (isoDate: string | null): AsyncState<{ items: TestRun[] }> => {
  const from = isoDate ? new Date(isoDate) : null;
  from?.setHours(0, 0, 0, 0);
  const to = from ? new Date(from) : null;
  to?.setHours(23, 59, 59, 999);

  return useAsync(
    () =>
      runService.list({
        from: from?.toISOString(),
        to: to?.toISOString(),
        sort: 'started_at',
        direction: 'asc',
        limit: 200,
      }),
    [isoDate],
    isoDate !== null,
  );
};
