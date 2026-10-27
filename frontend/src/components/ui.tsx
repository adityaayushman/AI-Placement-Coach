import type { ReactNode } from "react";

export function Panel({
  title,
  eyebrow,
  action,
  children,
  className = "",
}: {
  title?: string;
  eyebrow?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`glass p-5 sm:p-6 ${className}`}>
      {(title || action) && (
        <header className="mb-4 flex items-start justify-between gap-4">
          <div>
            {eyebrow && <p className="eyebrow">{eyebrow}</p>}
            {title && <h2 className="mt-1 font-serif text-xl text-ink">{title}</h2>}
          </div>
          {action}
        </header>
      )}
      {children}
    </section>
  );
}

export function PageHeader({ title, lede }: { title: string; lede?: string }) {
  return (
    <header className="mb-8">
      <h1 className="font-serif text-3xl tracking-tight text-ink sm:text-4xl">{title}</h1>
      {lede && <p className="mt-2 max-w-2xl text-muted">{lede}</p>}
    </header>
  );
}

export function Loading({ label = "Loading" }: { label?: string }) {
  return (
    <div role="status" className="flex items-center gap-3 py-8 text-muted">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-line border-t-amber" />
      {label}
    </div>
  );
}

export function ErrorNote({ error }: { error: unknown }) {
  if (!error) return null;
  const message = error instanceof Error ? error.message : "Something went wrong.";
  return (
    <p role="alert" className="rounded-xl border border-[rgba(229,138,122,0.45)] bg-[rgba(229,138,122,0.12)] px-4 py-3 text-sm text-ink">
      {message}
    </p>
  );
}

export function Empty({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="rounded-xl border border-dashed border-line px-5 py-8 text-center">
      <p className="font-serif text-lg text-ink">{title}</p>
      {children && <div className="mt-2 text-sm text-muted">{children}</div>}
    </div>
  );
}

export function Meter({ label, value, hint }: { label: string; value: number | null; hint?: string }) {
  return (
    <div>
      <div className="flex items-baseline justify-between text-sm">
        <span className="text-ink">{label}</span>
        <span className="tabular-nums text-muted">{value === null ? "No data" : Math.round(value)}</span>
      </div>
      <div
        className="mt-2 h-2 overflow-hidden rounded-full bg-white/5"
        role="meter"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={value ?? undefined}
      >
        <div
          className="h-full rounded-full bg-gradient-to-r from-mauve via-rose to-amber transition-[width] duration-300"
          style={{ width: `${value ?? 0}%` }}
        />
      </div>
      {hint && <p className="mt-1 text-xs text-faint">{hint}</p>}
    </div>
  );
}

export function ScoreRing({ score, size = 168 }: { score: number | null; size?: number }) {
  const r = size / 2 - 12;
  const c = 2 * Math.PI * r;
  const pct = score === null ? 0 : Math.max(0, Math.min(100, score)) / 100;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img"
      aria-label={score === null ? "No readiness score yet" : `Readiness score ${Math.round(score)} out of 100`}>
      <defs>
        <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="var(--mauve)" />
          <stop offset="55%" stopColor="var(--rose)" />
          <stop offset="100%" stopColor="var(--amber)" />
        </linearGradient>
      </defs>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,240,225,0.08)" strokeWidth={10} />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke="url(#ring)"
        strokeWidth={10}
        strokeLinecap="round"
        strokeDasharray={c}
        strokeDashoffset={c * (1 - pct)}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{ transition: "stroke-dashoffset 600ms ease" }}
      />
      <text x="50%" y="50%" textAnchor="middle" dominantBaseline="central"
        className="fill-[var(--ink)] font-serif" fontSize={size / 3.6}>
        {score === null ? "–" : Math.round(score)}
      </text>
    </svg>
  );
}

export function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: ReactNode;
  hint?: string;
}) {
  return (
    <label className="block">
      <span className="label">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-faint">{hint}</span>}
    </label>
  );
}
