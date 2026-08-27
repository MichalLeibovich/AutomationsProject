import type { RunStatus, TestRun } from './run.types';

export interface Paginated<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export type RunSortField = 'started_at' | 'duration_seconds' | 'status';
export type SortDirection = 'asc' | 'desc';
export type StatusFilter = RunStatus | 'all';

export interface RunListParams {
  scope?: string | null;
  status?: StatusFilter;
  search?: string;
  from?: string;
  to?: string;
  sort?: RunSortField;
  direction?: SortDirection;
  limit?: number;
  offset?: number;
}

export type RangePreset = 'hour' | 'day' | 'week' | 'custom';

export interface DashboardParams {
  scope?: string | null;
  range: RangePreset;
  from?: string;
  to?: string;
}

export interface DashboardStats {
  totalRuns: number;
  failedRuns: number;
  passRate: number;
  averageDurationSeconds: number;
}

export interface VolumePoint {
  label: string;
  bucketStart: string;
  passed: number;
  failed: number;
}

export interface NamedCount {
  name: string;
  count: number;
  color: string | null;
}

export interface DashboardResponse {
  stats: DashboardStats;
  volume: VolumePoint[];
  failuresByFeature: NamedCount[];
  failuresByErrorType: NamedCount[];
}

export interface CalendarDay {
  date: string;
  total: number;
  passed: number;
  failed: number;
  preview: Pick<TestRun, 'id' | 'scopeLabel' | 'status'>[];
}

/** Uniform error envelope emitted by the Flask API. */
export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: Record<string, string[]>;
    correlationId: string;
  };
}
