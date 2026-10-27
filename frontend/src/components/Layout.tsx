import { NavLink, Outlet } from "react-router-dom";

import ApiStatus from "./ApiStatus";

const upcoming = ["Resume", "Interview", "Plan"];

export default function Layout() {
  return (
    <div className="flex min-h-screen flex-col bg-paper text-ink">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:bg-paper focus:px-3 focus:py-2"
      >
        Skip to content
      </a>
      <header className="mx-auto flex w-full max-w-3xl items-baseline justify-between px-6 pt-8">
        <NavLink to="/" className="font-serif text-lg tracking-tight">
          Placement Coach
        </NavLink>
        <nav aria-label="Primary" className="flex gap-6 text-sm">
          <NavLink to="/" end className={({ isActive }) => (isActive ? "text-ink" : "text-muted")}>
            Overview
          </NavLink>
          {upcoming.map((label) => (
            <span key={label} className="cursor-default text-muted/60" title="Not built yet">
              {label}
            </span>
          ))}
        </nav>
      </header>
      <main id="main" className="mx-auto w-full max-w-3xl flex-1 px-6 py-16">
        <Outlet />
      </main>
      <footer className="mx-auto w-full max-w-3xl border-t border-line px-6 py-6 text-sm text-muted">
        <ApiStatus />
      </footer>
    </div>
  );
}
