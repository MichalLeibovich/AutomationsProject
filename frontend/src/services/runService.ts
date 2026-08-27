/** Run triggering, history, steps, comments, artifacts and export requests. */

import { apiClient } from '@/api/client';
import { endpoints } from '@/api/endpoints';
import type { Paginated, RunListParams } from '@/types/api.types';
import type { RunArtifact, RunComment, RunStep, TestRun } from '@/types/run.types';

/**
 * Recorded as the trigger source on runs started from the interface.
 *
 * There are no accounts, so `triggeredBy` is free text. Sending a fixed label
 * keeps dashboard-initiated runs distinguishable from scheduled or CI ones.
 */
const UI_TRIGGERED_BY = 'dashboard';

export const runService = {
  /**
   * Fetch a page of run history.
   *
   * @param params - Scope, status, search, date bounds, sorting and pagination.
   * @returns The page, with the total match count so the interface can show how
   * many rows remain.
   * @throws {ApiError} If a parameter is rejected or the request fails.
   */
  async list(params: RunListParams): Promise<Paginated<TestRun>> {
    const { data } = await apiClient.get<Paginated<TestRun>>(endpoints.runs.list, { params });
    return data;
  },

  /**
   * Fetch one run.
   *
   * @param runId - The run's identifier.
   * @returns The run.
   * @throws {ApiError} If the run does not exist.
   */
  async getById(runId: string): Promise<TestRun> {
    const { data } = await apiClient.get<TestRun>(endpoints.runs.byId(runId));
    return data;
  },

  /**
   * Trigger one automation run.
   *
   * The idempotency key is generated here rather than by the caller, so every
   * trigger path gets the protection automatically: a double-click or a retried
   * submit returns the original run instead of enqueueing a second.
   *
   * @param testDefinitionId - The automation to run.
   * @returns The queued run.
   * @throws {ApiError} If the automation is unknown or inactive.
   */
  async start(testDefinitionId: string): Promise<TestRun> {
    const { data } = await apiClient.post<TestRun>(endpoints.runs.create, {
      testDefinitionId,
      idempotencyKey: crypto.randomUUID(),
      triggeredBy: UI_TRIGGERED_BY,
      triggerSource: 'manual',
    });
    return data;
  },

  /**
   * Trigger the main automation of every application in scope.
   *
   * @param scope - Null for all applications, or an application name. The
   * general scope is refused by the API, which is why the interface hides the
   * control there.
   * @returns The queued runs.
   * @throws {ApiError} If the scope is the general scope.
   */
  async startBulkMain(scope: string | null): Promise<TestRun[]> {
    const { data } = await apiClient.post<{ started: TestRun[] }>(endpoints.runs.bulk, {
      scope,
      idempotencyKey: crypto.randomUUID(),
      triggeredBy: UI_TRIGGERED_BY,
    });
    return data.started;
  },

  /**
   * Cancel an in-flight run.
   *
   * @param runId - The run to cancel.
   * @returns The cancelled run.
   * @throws {ApiError} If the run already finished.
   */
  async cancel(runId: string): Promise<TestRun> {
    const { data } = await apiClient.post<TestRun>(endpoints.runs.cancel(runId), {
      actorName: UI_TRIGGERED_BY,
    });
    return data;
  },

  /**
   * Fetch a run's per-step detail.
   *
   * @param runId - The run whose steps to fetch.
   * @returns Steps in execution order, empty when the runner reported none.
   * @throws {ApiError} If the request fails.
   */
  async listSteps(runId: string): Promise<RunStep[]> {
    const { data } = await apiClient.get<RunStep[]>(endpoints.runs.steps(runId));
    return data;
  },

  /**
   * List a run's artifacts.
   *
   * @param runId - The run whose artifacts to fetch.
   * @returns Artifacts, each with a download path when the file is reachable.
   * @throws {ApiError} If the request fails.
   */
  async listArtifacts(runId: string): Promise<RunArtifact[]> {
    const { data } = await apiClient.get<RunArtifact[]>(endpoints.runs.artifacts(runId));
    return data;
  },

  /**
   * List a run's comments.
   *
   * @param runId - The run whose comments to fetch.
   * @returns Comments, oldest first.
   * @throws {ApiError} If the request fails.
   */
  async listComments(runId: string): Promise<RunComment[]> {
    const { data } = await apiClient.get<RunComment[]>(endpoints.runs.comments(runId));
    return data;
  },

  /**
   * Add a comment to a run.
   *
   * @param runId - The run being commented on.
   * @param body - Comment text.
   * @param authorName - Name to record. Free text, since there are no accounts.
   * @returns The created comment.
   * @throws {ApiError} If the text is rejected.
   */
  async addComment(runId: string, body: string, authorName: string): Promise<RunComment> {
    const { data } = await apiClient.post<RunComment>(endpoints.runs.comments(runId), {
      body,
      authorName,
    });
    return data;
  },

  /**
   * Remove a comment.
   *
   * @param runId - The run the comment belongs to.
   * @param commentId - The comment to remove.
   * @throws {ApiError} If the comment does not exist.
   */
  async deleteComment(runId: string, commentId: string): Promise<void> {
    await apiClient.delete(endpoints.runs.comment(runId, commentId));
  },

  /**
   * Build the CSV export URL for the current filter.
   *
   * The API streams the file directly rather than queueing a job, so the browser
   * can download it by navigating — no polling, and no blob held in memory.
   *
   * @param params - The run filter to export.
   * @returns A URL suitable for a download link or `window.open`.
   */
  buildExportUrl(params: RunListParams): string {
    const query = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        query.set(key, String(value));
      }
    });

    const base = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '/api';
    return `${base}${endpoints.runs.export}?${query.toString()}`;
  },
};
