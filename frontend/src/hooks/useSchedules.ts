import { scheduleService } from '@/services/scheduleService';
import type { Schedule, ScheduledOccurrence, ScheduledRunGroup } from '@/types/schedule.types';
import { useAsync } from './useRuns';
import type { AsyncState } from './useRuns';

export const useSchedules = (): AsyncState<Schedule[]> =>
  useAsync(() => scheduleService.list(), []);

export const useUpcomingOccurrences = (hours = 24): AsyncState<ScheduledOccurrence[]> =>
  useAsync(() => scheduleService.listUpcoming(hours), [hours]);

export const useRecentScheduledRuns = (limit = 8): AsyncState<ScheduledRunGroup[]> =>
  useAsync(() => scheduleService.listRecent(limit), [limit]);
