import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeAll, beforeEach, expect, test, vi } from "vitest";

import App from "./App";
import { setTokens } from "./api/client";
import { AuthProvider } from "./auth/AuthContext";
import { encodeWavBuffer } from "./lib/wav";

type Routes = Record<string, unknown>;

function mockApi(routes: Routes) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => {
      const path = url.replace(/^.*\/api\/v1/, "").split("?")[0];
      if (path in routes) return { ok: true, status: 200, json: async () => routes[path] };
      return { ok: false, status: 404, json: async () => ({ detail: "not found" }) };
    }),
  );
}

function renderAt(path: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <MemoryRouter initialEntries={[path]}>
          <App />
        </MemoryRouter>
      </AuthProvider>
    </QueryClientProvider>,
  );
}

// Warm the lazily loaded dashboard (and Recharts) once, so tests measure rendering, not import time.
beforeAll(async () => {
  await import("./pages/Dashboard");
}, 60_000);

beforeEach(() => setTokens(null));
afterEach(() => vi.unstubAllGlobals());

test("signed-out visitors land on sign in", async () => {
  mockApi({});
  renderAt("/");
  expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument();
});

test("student dashboard shows score, synthetic label and recommendations", async () => {
  setTokens({ access_token: "a", refresh_token: "r", role: "student" });
  mockApi({
    "/auth/me": { id: 1, email: "s@example.com", full_name: "Sam", role: "student" },
    "/me/readiness": {
      latest: {
        id: 1, score: 64.2, probability: 0.6, model_version: "readiness-lr-x",
        components: { values: { predictor: 60, resume: 70, mastery: null, interview: null, consistency: 40 }, missing: ["mastery", "interview"], company_type: "product", data_source: "synthetic-v1" },
        weights: { predictor: 0.5, resume: 0.25, consistency: 0.25 },
        attributions: [{ feature: "cgpa", label: "CGPA", value: 8, baseline: 7, effect: 0.05 }],
        created_at: "2026-10-27T00:00:00Z",
      },
      history: [{ at: "2026-10-27T00:00:00Z", score: 64.2 }],
      change: { score: null, components: {} },
    },
    "/me/recommendations": [{ id: 9, skill: "system design", reason: "Estimated mastery 20%.", priority: 0.5, status: "open", resource: null }],
    "/me/mastery": [],
    "/announcements": [],
  });
  renderAt("/");
  expect(
    await screen.findByRole("img", { name: "Readiness score 64 out of 100" }, { timeout: 15000 }),
  ).toBeInTheDocument();
  expect(screen.getByText("Trained on synthetic data")).toBeInTheDocument();
  expect(await screen.findByText("system design")).toBeInTheDocument();
  expect(screen.getByText("CGPA")).toBeInTheDocument();
});

test("students are kept out of coordinator pages", async () => {
  setTokens({ access_token: "a", refresh_token: "r", role: "student" });
  mockApi({
    "/auth/me": { id: 1, email: "s@example.com", full_name: "Sam", role: "student" },
    "/me/readiness": { latest: null, history: [], change: { score: null, components: {} } },
    "/me/recommendations": [], "/me/mastery": [], "/announcements": [],
  });
  renderAt("/coordinator");
  expect(
    await screen.findByRole("heading", { name: "Your readiness" }, { timeout: 15000 }),
  ).toBeInTheDocument();
});

test("wav encoder writes a valid 16-bit PCM header", () => {
  const view = new DataView(encodeWavBuffer(new Float32Array([0, 0.5, -0.5, 1]), 16000));
  const tag = (o: number) => String.fromCharCode(...[0, 1, 2, 3].map((i) => view.getUint8(o + i)));
  expect(tag(0)).toBe("RIFF");
  expect(tag(8)).toBe("WAVE");
  expect(view.getUint16(34, true)).toBe(16);
  expect(view.getUint32(24, true)).toBe(16000);
  expect(view.getUint32(40, true)).toBe(8);
  expect(view.getInt16(50, true)).toBe(32767);
});
