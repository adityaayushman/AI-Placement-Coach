import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { api } from "../api/client";
import type { Announcement, Mastery, Readiness, Recommendation } from "../api/types";
import Icon from "../components/Icon";
import { Empty, ErrorNote, Loading, Meter, PageHeader, Panel, ScoreRing } from "../components/ui";

const COMPONENTS: Record<string, { label: string; hint: string }> = {
  predictor: { label: "Predicted readiness", hint: "Model estimate from your profile and activity" },
  resume: { label: "Resume", hint: "ATS checks and keyword coverage" },
  mastery: { label: "Skill mastery", hint: "From quizzes and interview answers" },
  interview: { label: "Mock interviews", hint: "Average of your last 10 answers" },
  consistency: { label: "Consistency", hint: "Active days in the last four weeks" },
};

export default function Dashboard() {
  const qc = useQueryClient();
  const readiness = useQuery({ queryKey: ["readiness"], queryFn: () => api<Readiness>("/me/readiness") });
  const recs = useQuery({ queryKey: ["recs"], queryFn: () => api<Recommendation[]>("/me/recommendations") });
  const mastery = useQuery({ queryKey: ["mastery"], queryFn: () => api<Mastery[]>("/me/mastery") });
  const news = useQuery({ queryKey: ["announcements"], queryFn: () => api<Announcement[]>("/announcements") });
  const refresh = useMutation({
    mutationFn: () => api<Readiness>("/me/readiness/refresh", { method: "POST" }),
    onSuccess: (d) => qc.setQueryData(["readiness"], d),
  });
  const setStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      api(`/me/recommendations/${id}`, { method: "PATCH", json: { status } }),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["recs"] });
      void qc.invalidateQueries({ queryKey: ["mastery"] });
    },
  });

  if (readiness.isPending) return <Loading label="Loading your readiness" />;
  if (readiness.isError) return <ErrorNote error={readiness.error} />;
  const latest = readiness.data.latest;
  const change = readiness.data.change.score;
  const synthetic = latest?.components.data_source?.startsWith("synthetic");

  return (
    <>
      <PageHeader title="Your readiness" lede="One score, the parts behind it, and what to do next." />

      <div className="grid gap-6 xl:grid-cols-3">
        <Panel className="xl:col-span-1" eyebrow="Placement readiness"
          action={
            <button type="button" className="btn-ghost px-3" onClick={() => refresh.mutate()} disabled={refresh.isPending}>
              {refresh.isPending ? "Scoring" : "Rescore"}
            </button>
          }>
          <div className="flex flex-col items-center gap-3 py-2">
            <ScoreRing score={latest?.score ?? null} />
            {latest ? (
              <p className="text-sm text-muted">
                {change === null ? "First score recorded." : change === 0 ? "No change since last time."
                  : <><span className={change > 0 ? "text-ok" : "text-danger"}>{change > 0 ? "+" : ""}{change}</span> since last time</>}
              </p>
            ) : (
              <p className="text-center text-sm text-muted">
                Add your profile details to get a first score. <Link className="text-amber hover:underline" to="/profile">Open profile</Link>
              </p>
            )}
          </div>
          {latest && (
            <p className="mt-4 border-t border-line pt-4 text-xs text-faint">
              Model {latest.model_version}
              {synthetic && <span className="chip ml-2 align-middle">Trained on synthetic data</span>}
            </p>
          )}
        </Panel>

        <Panel className="xl:col-span-2" eyebrow="Breakdown" title="What makes up your score">
          {latest ? (
            <div className="grid gap-5 sm:grid-cols-2">
              {Object.entries(COMPONENTS).map(([key, meta]) => (
                <Meter key={key} label={meta.label} value={latest.components.values[key] ?? null}
                  hint={latest.weights[key] ? `${meta.hint}. Weight ${Math.round(latest.weights[key] * 100)}%.`
                    : `${meta.hint}. Not counted yet.`} />
              ))}
            </div>
          ) : (
            <Empty title="No score yet">Your breakdown appears after the first score.</Empty>
          )}
        </Panel>

        <Panel className="xl:col-span-2" eyebrow="Trend" title="Score over time">
          {readiness.data.history.length > 1 ? (
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={readiness.data.history.map((h) => ({ ...h, label: new Date(h.at).toLocaleDateString() }))}>
                  <defs>
                    <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#e2b062" stopOpacity={0.45} />
                      <stop offset="100%" stopColor="#a77b8e" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="label" stroke="#9a8a7b" tickLine={false} axisLine={false} fontSize={12} minTickGap={24} />
                  <YAxis domain={[0, 100]} stroke="#9a8a7b" tickLine={false} axisLine={false} fontSize={12} width={32} />
                  <Tooltip contentStyle={{ background: "rgba(33,25,21,0.92)", border: "1px solid rgba(244,228,210,0.14)", borderRadius: 12, color: "#f4ebe1" }} />
                  <Area type="monotone" dataKey="score" stroke="#e2b062" strokeWidth={2} fill="url(#trendFill)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <Empty title="One point so far">Your trend line starts after your next update.</Empty>
          )}
        </Panel>

        <Panel eyebrow="Drivers" title="What moved the prediction">
          {latest?.attributions.length ? (
            <ul className="space-y-3">
              {latest.attributions.slice(0, 6).map((a) => (
                <li key={a.feature} className="flex items-center justify-between gap-4 text-sm">
                  <span className="text-ink">{a.label}</span>
                  <span className={`tabular-nums ${a.effect >= 0 ? "text-ok" : "text-danger"}`}>
                    {a.effect >= 0 ? "+" : ""}{(a.effect * 100).toFixed(1)} pts
                  </span>
                </li>
              ))}
              <li className="pt-2 text-xs text-faint">
                Change in predicted probability against a typical student. Approximate, not SHAP.
              </li>
            </ul>
          ) : (
            <Empty title="No drivers yet" />
          )}
        </Panel>

        <Panel className="xl:col-span-2" eyebrow="This week" title="Work on these next">
          {recs.isPending ? <Loading /> : recs.isError ? <ErrorNote error={recs.error} /> : recs.data.length ? (
            <ul className="space-y-3">
              {recs.data.map((r) => (
                <li key={r.id} className="rounded-2xl border border-line bg-white/[0.03] p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="font-serif text-lg capitalize text-ink">{r.skill}</p>
                      <p className="mt-1 text-sm text-muted">{r.reason}</p>
                      {r.resource && (
                        <a href={r.resource.url} target="_blank" rel="noreferrer"
                          className="mt-2 inline-flex items-center gap-1 text-sm text-amber hover:underline">
                          {r.resource.title} · {r.resource.minutes} min <Icon name="arrow" size={14} />
                        </a>
                      )}
                    </div>
                    <div className="flex gap-2">
                      {r.status === "open" && (
                        <button type="button" className="btn-ghost px-4" onClick={() => setStatus.mutate({ id: r.id, status: "accepted" })}>
                          Start
                        </button>
                      )}
                      <button type="button" className="btn-ghost px-4" aria-label={`Mark ${r.skill} done`}
                        onClick={() => setStatus.mutate({ id: r.id, status: "completed" })}>
                        <Icon name="check" size={16} /> Done
                      </button>
                      <button type="button" className="btn-ghost px-3" aria-label={`Skip ${r.skill}`}
                        onClick={() => setStatus.mutate({ id: r.id, status: "ignored" })}>
                        <Icon name="x" size={16} />
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <Empty title="Nothing queued">Take a quiz so we can find your gaps.</Empty>
          )}
        </Panel>

        <Panel eyebrow="Mastery" title="Skills tracked">
          {mastery.data?.length ? (
            <div className="space-y-4">
              {mastery.data.slice(0, 8).map((m) => (
                <Meter key={m.skill} label={m.skill} value={m.p_known * 100} hint={`${m.n_obs} answers`} />
              ))}
            </div>
          ) : (
            <Empty title="No skills tracked yet"><Link className="text-amber hover:underline" to="/practice">Take a quiz</Link></Empty>
          )}
        </Panel>

        {news.data && news.data.length > 0 && (
          <Panel className="xl:col-span-3" eyebrow="From your placement cell" title="Announcements">
            <ul className="grid gap-3 md:grid-cols-2">
              {news.data.slice(0, 4).map((a) => (
                <li key={a.id} className="rounded-2xl border border-line bg-white/[0.03] p-4">
                  <p className="text-ink">{a.title}</p>
                  <p className="mt-1 text-sm text-muted">{a.body}</p>
                </li>
              ))}
            </ul>
          </Panel>
        )}
      </div>
    </>
  );
}
