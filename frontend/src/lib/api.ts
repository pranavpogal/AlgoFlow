const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  details: unknown;

  constructor(path: string, status: number, details: unknown) {
    super(`API ${path} failed with status ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store"
  });
  if (!response.ok) throw new ApiError(path, response.status, await safeJson(response));
  return response.json();
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!response.ok) throw new ApiError(path, response.status, await safeJson(response));
  return response.json();
}

export function apiErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const details = error.details as { error?: { message?: string; code?: string } } | null;
    const message = details?.error?.message ?? `Request failed with status ${error.status}.`;
    const code = details?.error?.code ? ` (${details.error.code})` : "";
    return `${message}${code}`;
  }
  if (error instanceof Error) return error.message;
  return "The request failed unexpectedly.";
}

async function safeJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    return null;
  }
}
