import { apiClient } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import type { Application, TestDefinition } from '@/types/application.types';

export const catalogService = {
  async listApplications(): Promise<Application[]> {
    const { data } = await apiClient.get<Application[]>(endpoints.applications.list);
    return data;
  },

  /**
   * `scope` mirrors the UI selection:
   *   null      → application-scoped definitions only
   *   'general' → general automation only
   *   <name>    → that application's definitions
   */
  async listTestDefinitions(scope: string | null): Promise<TestDefinition[]> {
    const { data } = await apiClient.get<TestDefinition[]>(endpoints.testDefinitions.list, {
      params: scope ? { scope } : undefined,
    });
    return data;
  },

  async createApplication(payload: {
    name: string;
    slug: string;
    color: string;
    displayOrder?: number;
  }): Promise<Application> {
    const { data } = await apiClient.post<Application>(endpoints.applications.create, payload);
    return data;
  },

  async updateApplication(
    applicationId: string,
    payload: Partial<Pick<Application, 'name' | 'color' | 'displayOrder' | 'isActive'>>,
  ): Promise<Application> {
    const { data } = await apiClient.put<Application>(
      endpoints.applications.byId(applicationId),
      payload,
    );
    return data;
  },

  async deleteApplication(applicationId: string): Promise<void> {
    await apiClient.delete(endpoints.applications.byId(applicationId));
  },
};
