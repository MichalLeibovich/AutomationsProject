import { apiClient } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import type { CalendarDay, DashboardParams, DashboardResponse } from '@/types/api.types';

export const analyticsService = {
  async getDashboard(params: DashboardParams): Promise<DashboardResponse> {
    const { data } = await apiClient.get<DashboardResponse>(endpoints.analytics.dashboard, {
      params,
    });
    return data;
  },

  /** `month` is 1-based, matching the API rather than JavaScript's Date. */
  async getCalendarMonth(year: number, month: number): Promise<CalendarDay[]> {
    const { data } = await apiClient.get<CalendarDay[]>(endpoints.analytics.calendar, {
      params: { year, month },
    });
    return data;
  },
};
