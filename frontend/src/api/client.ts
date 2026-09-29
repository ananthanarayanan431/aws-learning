import type { ErrorResponse, SuccessResponse } from '../types'

export class ApiError extends Error {
  status: number
  code: string
  details?: unknown

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message)
    this.status = status
    this.code = code
    this.details = details
  }
}

const BASE = '/api/v1'

/** Calls the API and unwraps the SuccessResponse envelope, throwing ApiError on ErrorResponse. */
export async function request<T>(path: string, init?: RequestInit): Promise<SuccessResponse<T>> {
  let res: Response
  try {
    res = await fetch(BASE + path, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
    })
  } catch {
    throw new ApiError(0, 'NETWORK_ERROR', 'Cannot reach the server')
  }

  let body: SuccessResponse<T> | ErrorResponse
  try {
    body = await res.json()
  } catch {
    throw new ApiError(res.status, 'BAD_RESPONSE', 'Server returned an unexpected response')
  }

  if (!body.success) {
    throw new ApiError(res.status, body.error.code, body.message, body.error.details)
  }
  return body
}
