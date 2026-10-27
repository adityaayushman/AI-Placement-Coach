import { previewApi, previewRole } from "./preview";

const API_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";
const BASE = `${API_URL}/api/v1`;
const STORE_KEY = "pc.tokens";

export type Role = "student" | "coordinator" | "admin";

export interface Tokens {
  access_token: string;
  refresh_token: string;
  role: Role;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

let tokens: Tokens | null = readTokens();
const listeners = new Set<(t: Tokens | null) => void>();

function readTokens(): Tokens | null {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    return raw ? (JSON.parse(raw) as Tokens) : null;
  } catch {
    return null;
  }
}

export function getTokens(): Tokens | null {
  return tokens;
}

export function setTokens(next: Tokens | null): void {
  tokens = next;
  try {
    if (next) localStorage.setItem(STORE_KEY, JSON.stringify(next));
    else localStorage.removeItem(STORE_KEY);
  } catch {
    /* storage unavailable: keep tokens in memory only */
  }
  listeners.forEach((l) => l(next));
}

export function onTokens(listener: (t: Tokens | null) => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

async function refresh(): Promise<boolean> {
  if (!tokens) return false;
  const res = await fetch(`${BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: tokens.refresh_token }),
  });
  if (!res.ok) {
    setTokens(null);
    return false;
  }
  setTokens((await res.json()) as Tokens);
  return true;
}

interface Options {
  method?: string;
  json?: unknown;
  form?: FormData;
  raw?: boolean;
}

export async function api<T>(path: string, opts: Options = {}, retried = false): Promise<T> {
  if (previewRole()) {
    if (opts.raw) throw new ApiError(400, "Downloads need the live API. They are not available in preview.");
    return (await previewApi(path, opts)) as T;
  }
  const headers: Record<string, string> = {};
  if (tokens) headers.Authorization = `Bearer ${tokens.access_token}`;
  if (opts.json !== undefined) headers["Content-Type"] = "application/json";
  const res = await fetch(`${BASE}${path}`, {
    method: opts.method ?? (opts.json !== undefined || opts.form ? "POST" : "GET"),
    headers,
    body: opts.form ?? (opts.json !== undefined ? JSON.stringify(opts.json) : undefined),
  });
  if (res.status === 401 && tokens && !retried && (await refresh())) {
    return api<T>(path, opts, true);
  }
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === "string") message = body.detail;
      else if (Array.isArray(body.detail)) message = "Check the highlighted fields and try again.";
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, message);
  }
  if (opts.raw) return (await res.blob()) as T;
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export async function getHealth(): Promise<{ status: string }> {
  const res = await fetch(`${BASE}/health`);
  if (!res.ok) throw new Error(`API responded ${res.status}`);
  return (await res.json()) as { status: string };
}
