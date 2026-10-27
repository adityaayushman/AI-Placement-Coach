import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import Icon, { type IconName } from "./Icon";

const NAV: Record<string, { to: string; label: string; icon: IconName }[]> = {
  student: [
    { to: "/", label: "Overview", icon: "dashboard" },
    { to: "/profile", label: "Profile", icon: "user" },
    { to: "/resume", label: "Resume", icon: "file" },
    { to: "/practice", label: "Practice", icon: "checks" },
    { to: "/interview", label: "Interview", icon: "mic" },
    { to: "/privacy", label: "Privacy", icon: "shield" },
  ],
  coordinator: [{ to: "/coordinator", label: "Cohort", icon: "users" }],
  admin: [
    { to: "/coordinator", label: "Cohort", icon: "users" },
    { to: "/admin", label: "Admin", icon: "sliders" },
  ],
};

export default function Shell() {
  const { user, logout } = useAuth();
  const items = NAV[user?.role ?? "student"];

  return (
    <div className="min-h-screen text-ink">
      <a href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-full focus:bg-[var(--bg)] focus:px-4 focus:py-2">
        Skip to content
      </a>
      <div className="mx-auto flex max-w-7xl gap-6 px-4 py-4 sm:px-6 lg:py-6">
        <aside className="glass sticky top-6 hidden h-[calc(100vh-3rem)] w-60 shrink-0 flex-col p-4 lg:flex">
          <Brand />
          <nav aria-label="Primary" className="mt-8 flex flex-col gap-1">
            {items.map((item) => <NavItem key={item.to} {...item} />)}
          </nav>
          <div className="mt-auto border-t border-line pt-4">
            <p className="truncate text-sm text-ink">{user?.full_name || user?.email}</p>
            <p className="text-xs capitalize text-faint">{user?.role}</p>
            <button type="button" onClick={logout} className="btn-ghost mt-3 w-full">
              <Icon name="logout" size={16} /> Sign out
            </button>
          </div>
        </aside>

        <div className="min-w-0 flex-1">
          <header className="glass mb-6 flex items-center justify-between px-4 py-3 lg:hidden">
            <Brand />
            <button type="button" onClick={logout} className="btn-ghost px-3" aria-label="Sign out">
              <Icon name="logout" size={16} />
            </button>
          </header>
          <nav aria-label="Primary mobile" className="glass mb-6 flex gap-1 overflow-x-auto p-1.5 lg:hidden">
            {items.map((item) => <NavItem key={item.to} {...item} compact />)}
          </nav>
          <main id="main" className="pb-16">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}

function Brand() {
  return (
    <div className="flex items-center gap-2.5">
      <span aria-hidden="true"
        className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-mauve via-rose to-amber font-serif text-lg text-[#1d1511]">
        P
      </span>
      <span className="font-serif text-lg leading-tight">Placement Coach</span>
    </div>
  );
}

function NavItem({ to, label, icon, compact }: { to: string; label: string; icon: IconName; compact?: boolean }) {
  return (
    <NavLink
      to={to}
      end={to === "/"}
      className={({ isActive }) =>
        `flex min-h-[44px] shrink-0 cursor-pointer items-center gap-3 rounded-xl px-3 text-sm transition-colors duration-200 ${
          isActive ? "bg-white/10 text-ink" : "text-muted hover:bg-white/5 hover:text-ink"
        } ${compact ? "px-3" : ""}`
      }
    >
      <Icon name={icon} />
      {label}
    </NavLink>
  );
}
