import type { Job, JobCreate } from "./types";

// Empty = same origin, proxied to the API by next.config.ts rewrites.
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}/api/v1${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const detail = body?.detail;
    const message = Array.isArray(detail)
      ? detail.map((d: { msg: string }) => d.msg.replace(/^Value error, /, "")).join(" · ")
      : (detail ?? `Request failed (${res.status})`);
    throw new ApiError(message, res.status);
  }
  return res.json() as Promise<T>;
}

export const api = {
  createJob: (body: JobCreate) =>
    request<{ id: string; status: string }>("/jobs", { method: "POST", body: JSON.stringify(body) }),
  getJob: (id: string) => request<Job>(`/jobs/${id}`),
  eventsUrl: (id: string) => `${API_BASE}/api/v1/jobs/${id}/events`,
  mediaUrl: (path: string) => (path.startsWith("http") ? path : `${API_BASE}${path}`),
};
