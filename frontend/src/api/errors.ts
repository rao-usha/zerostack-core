/**
 * API Error handling utilities.
 * Provides standardized error extraction, formatting, and types.
 */
import { AxiosError } from 'axios'

/**
 * Expected API error response shape from FastAPI.
 */
interface ApiErrorResponse {
  detail?: string | Array<{ msg?: string; message?: string; loc?: string[] }>
  message?: string
  error?: string
  code?: string
  [key: string]: unknown
}

/**
 * Standard API error structure.
 */
export interface ApiError {
  message: string
  code?: string
  status?: number
  details?: Record<string, unknown>
  isNetworkError: boolean
  isTimeout: boolean
  isServerError: boolean
  isClientError: boolean
  isAuthError: boolean
  retry?: () => Promise<unknown>
}

/**
 * Error messages for common HTTP status codes.
 */
const STATUS_MESSAGES: Record<number, string> = {
  400: 'Invalid request. Please check your input.',
  401: 'Please log in to continue.',
  403: 'You do not have permission to perform this action.',
  404: 'The requested resource was not found.',
  408: 'Request timed out. Please try again.',
  409: 'A conflict occurred. The resource may have been modified.',
  422: 'The provided data is invalid.',
  429: 'Too many requests. Please wait a moment and try again.',
  500: 'An unexpected server error occurred.',
  502: 'Service temporarily unavailable.',
  503: 'Service is currently unavailable. Please try again later.',
  504: 'Request timed out. Please try again.',
}

/**
 * Extract a user-friendly error message from various error types.
 */
export function extractErrorMessage(error: unknown): string {
  // Axios error
  if (isAxiosError(error)) {
    // Network error (no response)
    if (!error.response) {
      if (error.code === 'ECONNABORTED') {
        return 'Request timed out. Please check your connection and try again.'
      }
      return 'Unable to connect to the server. Please check your internet connection.'
    }

    // Server responded with error
    const { status } = error.response
    const data = error.response.data as ApiErrorResponse | undefined

    // Try to extract message from response data
    if (data) {
      // FastAPI error format
      if (typeof data.detail === 'string') {
        return data.detail
      }
      // FastAPI validation error format
      if (Array.isArray(data.detail)) {
        const messages = data.detail.map((err) =>
          err.msg || err.message || 'Validation error'
        )
        return messages.join('. ')
      }
      // Generic message field
      if (typeof data.message === 'string') {
        return data.message
      }
      // Error field
      if (typeof data.error === 'string') {
        return data.error
      }
    }

    // Fallback to status code message
    return STATUS_MESSAGES[status] || `Request failed with status ${status}`
  }

  // Standard Error object
  if (error instanceof Error) {
    return error.message
  }

  // String error
  if (typeof error === 'string') {
    return error
  }

  // Unknown error
  return 'An unexpected error occurred.'
}

/**
 * Parse an error into a standardized ApiError object.
 */
export function parseApiError(error: unknown, retryFn?: () => Promise<unknown>): ApiError {
  const message = extractErrorMessage(error)

  let code: string | undefined
  let status: number | undefined
  let details: Record<string, unknown> | undefined
  let isNetworkError = false
  let isTimeout = false
  let isServerError = false
  let isClientError = false
  let isAuthError = false

  if (isAxiosError(error)) {
    if (!error.response) {
      isNetworkError = true
      isTimeout = error.code === 'ECONNABORTED'
    } else {
      const data = error.response.data as ApiErrorResponse | undefined
      status = error.response.status
      code = data?.code
      details = data as Record<string, unknown> | undefined

      isServerError = status >= 500
      isClientError = status >= 400 && status < 500
      isAuthError = status === 401 || status === 403
    }
  }

  return {
    message,
    code,
    status,
    details,
    isNetworkError,
    isTimeout,
    isServerError,
    isClientError,
    isAuthError,
    retry: retryFn,
  }
}

/**
 * Type guard for Axios errors.
 */
export function isAxiosError(error: unknown): error is AxiosError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'isAxiosError' in error &&
    (error as AxiosError).isAxiosError === true
  )
}

/**
 * Check if an error is a network error (no response).
 */
export function isNetworkError(error: unknown): boolean {
  if (isAxiosError(error)) {
    return !error.response
  }
  return false
}

/**
 * Check if an error is an authentication error.
 */
export function isAuthenticationError(error: unknown): boolean {
  if (isAxiosError(error) && error.response) {
    return error.response.status === 401 || error.response.status === 403
  }
  return false
}

/**
 * Check if an error is a validation error.
 */
export function isValidationError(error: unknown): boolean {
  if (isAxiosError(error) && error.response) {
    return error.response.status === 422 || error.response.status === 400
  }
  return false
}

/**
 * Extract validation errors from a 422 response.
 */
export function extractValidationErrors(error: unknown): Record<string, string[]> {
  const errors: Record<string, string[]> = {}

  if (isAxiosError(error) && error.response) {
    const data = error.response.data as ApiErrorResponse | undefined
    const detail = data?.detail

    if (Array.isArray(detail)) {
      for (const err of detail) {
        // FastAPI validation error format: { loc: ['body', 'field'], msg: 'error message' }
        if (err.loc && Array.isArray(err.loc)) {
          const field = err.loc[err.loc.length - 1] || 'general'
          if (!errors[field]) {
            errors[field] = []
          }
          errors[field].push(err.msg || 'Invalid value')
        }
      }
    }
  }

  return errors
}

/**
 * Simple retry function with exponential backoff.
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  options: {
    maxRetries?: number
    initialDelayMs?: number
    maxDelayMs?: number
    shouldRetry?: (error: unknown, attempt: number) => boolean
  } = {}
): Promise<T> {
  const {
    maxRetries = 3,
    initialDelayMs = 1000,
    maxDelayMs = 10000,
    shouldRetry = (error) => isNetworkError(error),
  } = options

  let lastError: unknown

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error

      if (attempt === maxRetries || !shouldRetry(error, attempt)) {
        throw error
      }

      // Exponential backoff with jitter
      const delay = Math.min(
        initialDelayMs * Math.pow(2, attempt) + Math.random() * 1000,
        maxDelayMs
      )

      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }

  throw lastError
}

export default {
  extractErrorMessage,
  parseApiError,
  isAxiosError,
  isNetworkError,
  isAuthenticationError,
  isValidationError,
  extractValidationErrors,
  withRetry,
}
