import { API_BASE_URL, API_KEY } from '@/config/env';

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

function buildHeaders(extra?: Record<string, string>): Headers {
  return new Headers({
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
    ...extra,
  });
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    return response.json() as Promise<T>;
  }

  let code = `HTTP_${response.status}`;
  let message = response.statusText || 'An unexpected error occurred';

  try {
    const body = (await response.json()) as { code?: string; message?: string; detail?: string };
    if (body.code) code = body.code;
    if (body.message) message = body.message;
    else if (body.detail) message = body.detail;
  } catch {
    // Response body is not JSON; use defaults set above
  }

  throw new ApiError(response.status, code, message);
}

export async function apiGet<T>(path: string): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    method: 'GET',
    headers: buildHeaders(),
  });
  return handleResponse<T>(response);
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    method: 'POST',
    headers: buildHeaders(),
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });
  return handleResponse<T>(response);
}
