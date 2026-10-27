const API_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

export interface Health {
  status: string;
}

export async function getHealth(): Promise<Health> {
  const res = await fetch(`${API_URL}/api/v1/health`);
  if (!res.ok) throw new Error(`API responded ${res.status}`);
  return (await res.json()) as Health;
}
