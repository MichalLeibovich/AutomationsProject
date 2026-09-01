/** Scheduled-automation requests: upcoming/recent, skip/restore, extra runs. */

import { apiClient } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import type {
  Schedule,
  ScheduleExtraRun,
  ScheduledOccurrence,
  ScheduledRunGroup,
} from '@/types/schedule.types';

export const scheduleService = {
  /**
   * List every active recurring schedule.
   *
   * @returns The schedules.
   * @throws {ApiError} If the request fails.
   */
  async list(): Promise<Schedule[]> {
    const { data } = await apiClient.get<Schedule[]>(endpoints.schedules.list);
    return data;
  },

  /**
   * List every occurrence due in the next `hours`, including skipped ones.
   *
   * @param hours - How far ahead to look. Defaults to 24.
   * @returns Occurrences in ascending order.
   * @throws {ApiError} If the request fails.
   */
  async listUpcoming(hours = 24): Promise<ScheduledOccurrence[]> {
    const { data } = await apiClient.get<ScheduledOccurrence[]>(endpoints.schedules.upcoming, {
      params: { hours },
    });
    return data;
  },

  /**
   * List the most recently completed scheduled occurrences, grouped by slot.
   *
   * @param limit - Maximum groups to return. Defaults to 8.
   * @returns Groups, most recent first.
   * @throws {ApiError} If the request fails.
   */
  async listRecent(limit = 8): Promise<ScheduledRunGroup[]> {
    const { data } = await apiClient.get<ScheduledRunGroup[]>(endpoints.schedules.recent, {
      params: { limit },
    });
    return data;
  },

  /**
   * Change a recurring schedule's frequency.
   *
   * Does not touch the occurrence already committed under the current
   * cadence — the API pivots the change to take effect only after it.
   *
   * @param scheduleId - The schedule to update.
   * @param everyHours - The new interval between occurrences, in hours.
   * @returns The updated schedule.
   * @throws {ApiError} If the schedule does not exist, or `everyHours` is
   * not a whole-hour divisor of a day.
   */
  async updateFrequency(scheduleId: string, everyHours: number): Promise<Schedule> {
    const { data } = await apiClient.patch<Schedule>(endpoints.schedules.updateFrequency(scheduleId), {
      everyHours,
    });
    return data;
  },

  /**
   * Cancel one occurrence of a recurring schedule.
   *
   * @param scheduleId - The schedule the occurrence belongs to.
   * @param occurrenceAt - The occurrence to cancel, as returned by
   * {@link listUpcoming}.
   * @throws {ApiError} If the schedule does not exist.
   */
  async skip(scheduleId: string, occurrenceAt: string): Promise<void> {
    await apiClient.post(endpoints.schedules.skip(scheduleId), { occurrenceAt });
  },

  /**
   * Undo a skip.
   *
   * @param scheduleId - The schedule the occurrence belongs to.
   * @param occurrenceAt - The occurrence to restore.
   * @throws {ApiError} If the occurrence was not skipped.
   */
  async restore(scheduleId: string, occurrenceAt: string): Promise<void> {
    await apiClient.post(endpoints.schedules.restore(scheduleId), { occurrenceAt });
  },

  /**
   * Schedule one one-off run, outside any recurring schedule.
   *
   * @param applicationId - The application to run.
   * @param runAt - The instant to run it at, as an ISO string. Must be in
   * the future.
   * @returns The created extra run.
   * @throws {ApiError} If the application does not exist, or `runAt` is in
   * the past.
   */
  async addExtra(applicationId: string, runAt: string): Promise<ScheduleExtraRun> {
    const { data } = await apiClient.post<ScheduleExtraRun>(endpoints.schedules.createExtra, {
      applicationId,
      runAt,
    });
    return data;
  },

  /**
   * Remove a one-off run before it fires.
   *
   * @param extraRunId - The extra run to remove.
   * @throws {ApiError} If it does not exist, or had already fired.
   */
  async removeExtra(extraRunId: string): Promise<void> {
    await apiClient.delete(endpoints.schedules.deleteExtra(extraRunId));
  },
};
