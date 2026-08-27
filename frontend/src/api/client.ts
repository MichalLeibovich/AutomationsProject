/**
 * Configured Axios instance and the normalised error every request rejects with.
 *
 * Interceptors handle the two concerns that would otherwise be repeated in every
 * service: generating a correlation identifier, and translating a failure into
 * {@link ApiError}. There is no token handling — the API has no authentication.
 */

import axios from 'axios';
import type { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import type { ApiErrorBody } from '@/types/api.types';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '/api';
const TIMEOUT = Number(import.meta.env.VITE_API_TIMEOUT ?? 20_000);

/**
 * A request failure, in one shape regardless of cause.
 *
 * Hooks and components branch on {@link ApiError.status} and {@link ApiError.code}
 * rather than parsing Axios internals, so no caller needs to know how the
 * transport reports an error.
 */
export class ApiError extends Error {
  /** HTTP status, or 0 when no response arrived at all. */
  readonly status: number;
  /** Stable machine-readable code from the API envelope. */
  readonly code: string;
  /** Correlates this failure with the server logs. */
  readonly correlationId: string;
  /** Field-level validation errors, keyed by field name. */
  readonly details?: Record<string, string[]>;

  /**
   * @param status - HTTP status, or 0 for a transport failure.
   * @param code - Stable error code.
   * @param message - Hebrew message, safe to display.
   * @param correlationId - Identifier tying this failure to the server logs.
   * @param details - Field-level validation errors, when the API supplied any.
   */
  constructor(
    status: number,
    code: string,
    message: string,
    correlationId: string,
    details?: Record<string, string[]>,
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.correlationId = correlationId;
    this.details = details;
  }

  /**
   * Whether the request never reached the server.
   *
   * Worth distinguishing: an offline client needs a retry, whereas a rejected
   * request needs the user to change something.
   */
  get isNetworkError(): boolean {
    return this.status === 0;
  }
}

/**
 * Build the configured Axios instance.
 *
 * @returns An instance with the correlation and error interceptors installed.
 */
const createClient = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: BASE_URL,
    timeout: TIMEOUT,
    headers: { Accept: 'application/json' },
  });

  instance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    // Generated per request and echoed by the backend, so one user action can be
    // traced across the frontend, the API and the runner logs.
    config.headers['X-Correlation-Id'] = crypto.randomUUID();
    return config;
  });

  instance.interceptors.response.use(
    (response) => response,
    (error: AxiosError<ApiErrorBody>) => {
      // No response at all: DNS failure, timeout, or an offline client.
      if (!error.response) {
        return Promise.reject(
          new ApiError(0, 'network_error', 'לא ניתן להתחבר לשרת', 'unknown'),
        );
      }

      const { status, data, headers } = error.response;
      const envelope = data?.error;

      return Promise.reject(
        new ApiError(
          status,
          envelope?.code ?? `http_${status}`,
          envelope?.message ?? 'שגיאה בלתי צפויה',
          envelope?.correlationId ?? String(headers['x-correlation-id'] ?? 'unknown'),
          envelope?.details,
        ),
      );
    },
  );

  return instance;
};

/** The shared client. Every service issues requests through this instance. */
export const apiClient = createClient();
