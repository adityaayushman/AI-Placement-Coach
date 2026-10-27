import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import App from "./App";

afterEach(() => vi.unstubAllGlobals());

function renderAt(path: string) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[path]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

test("home renders with the service online", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: "ok" }) }));
  renderAt("/");
  expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(/know where you stand/i);
  expect(await screen.findByText("Service online")).toBeInTheDocument();
});

test("shows unreachable when the API fails", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("down")));
  renderAt("/");
  expect(await screen.findByText("Service unreachable")).toBeInTheDocument();
});

test("unknown route shows not found", () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("down")));
  renderAt("/nope");
  expect(screen.getByRole("heading", { name: "Page not found" })).toBeInTheDocument();
});
