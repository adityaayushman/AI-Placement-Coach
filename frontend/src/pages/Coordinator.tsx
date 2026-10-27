import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { api } from "../api/client";
import type { Announcement, Cohort, StudentRow } from "../api/types";
import Icon from "../components/Icon";
import { Empty, ErrorNote, Field, Loading, PageHeader, Panel } from "../components/ui";
import { useCountUp } from "../lib/motion";

const COMPONENTS = ["predictor", "resume", "mastery", "interview", "consistency"];

function heat(v: unknown): string {
  if (typeof v !== "number") return "transparent";
  return `rgba(226, 176, 98, ${0.08 + (v / 100) * 0.5})`;
}

export default function Coordinator() {
  const [type, setType] = useState("");
  const [atRisk, setAtRisk] = useState(false);
  const cohort = useQuery({
    queryKey: ["cohort", type],
    queryFn: () => api<Cohort>(`/coordinator/cohort${type ? `?company_type=${type}` : ""}`),
  });
  const students = useQuery({
    queryKey: ["consented", atRisk],
    queryFn: () => api<StudentRow[]>(`/coordinator/students?at_risk=${atRisk}`),
  });
  const exportCsv = useMutation({
    mutationFn: async () => {
      const blob = await api<Blob>("/coordinator/students.csv", { raw: true });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "consented-students.csv";
      a.click();
      URL.revokeObjectURL(url);
    },
  });

  if (cohort.isPending) return <Loading label="Loading cohort" />;
  if (cohort.isError) return <ErrorNote error={cohort.error} />;
  const c = cohort.data;

  return (
    <>
      <PageHeader title="Cohort overview" lede={`Groups smaller than ${c.min_group_size} are hidden. Individual rows only show students who allowed it.`} />
      <div className="mb-6 flex flex-wrap items-end gap-3">
        <div className="w-56">
          <Field label="Drive type">
            <select className="input" value={type} onChange={(e) => setType(e.target.value)}>
              <option value="">All students</option>
              <option value="product">Product-company aspirants</option>
              <option value="service">Service-company aspirants</option>
            </select>
          </Field>
        </div>
      </div>

      <div className="stagger grid gap-6 xl:grid-cols-4">
        {[
          ["Students", c.students],
          ["With a score", c.scored],
          ["Mean score", c.mean_score ?? "No data"],
          ["Below 50", c.at_risk_count],
        ].map(([label, value]) => (
          <Stat key={label} label={String(label)} value={value} />
        ))}

        <Panel title="Score distribution" className="xl:col-span-2">
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={c.distribution}>
                <XAxis dataKey="range" stroke="#9a8a7b" tickLine={false} axisLine={false} fontSize={11} />
                <YAxis allowDecimals={false} stroke="#9a8a7b" tickLine={false} axisLine={false} fontSize={11} width={28} />
                <Tooltip cursor={{ fill: "rgba(255,240,225,0.05)" }} contentStyle={{ background: "rgba(33,25,21,0.92)", border: "1px solid rgba(244,228,210,0.14)", borderRadius: 12, color: "#f4ebe1" }} />
                <Bar dataKey="count" fill="#d6a594" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Most common skill gaps" className="xl:col-span-2">
          {c.top_skill_gaps.length ? (
            <ul className="space-y-3">
              {c.top_skill_gaps.map((g) => (
                <li key={g.skill} className="flex items-center justify-between text-sm">
                  <span className="capitalize text-ink">{g.skill}</span>
                  <span className="tabular-nums text-muted">{g.students} students</span>
                </li>
              ))}
            </ul>
          ) : <Empty title="Not enough resumes yet" />}
        </Panel>

        <Panel title="Departments by component" className="xl:col-span-4">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="text-left text-faint">
                  <th className="py-2 font-medium">Department</th>
                  <th className="py-2 font-medium">n</th>
                  <th className="py-2 font-medium">Score</th>
                  {COMPONENTS.map((k) => <th key={k} className="py-2 font-medium capitalize">{k}</th>)}
                </tr>
              </thead>
              <tbody>
                {c.departments.map((d) => (
                  <tr key={d.department} className="border-t border-line">
                    <td className="py-2.5 text-ink">{d.department}</td>
                    <td className="py-2.5 tabular-nums text-muted">{d.n}</td>
                    {d.suppressed ? (
                      <td colSpan={COMPONENTS.length + 1} className="py-2.5 text-faint">Hidden: fewer than {c.min_group_size} students</td>
                    ) : (
                      <>
                        <td className="py-2.5 tabular-nums text-ink">{String(d.score)}</td>
                        {COMPONENTS.map((k) => (
                          <td key={k} className="py-1.5">
                            <span className="inline-block min-w-[3rem] rounded-lg px-2 py-1 tabular-nums text-ink" style={{ background: heat(d[k]) }}>
                              {typeof d[k] === "number" ? (d[k] as number).toFixed(0) : "–"}
                            </span>
                          </td>
                        ))}
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="Students who shared their results" className="xl:col-span-3"
          action={
            <div className="flex flex-wrap gap-2">
              <button type="button" className={atRisk ? "btn-primary" : "btn-ghost"} aria-pressed={atRisk} onClick={() => setAtRisk(!atRisk)}>
                Below 50 only
              </button>
              <button type="button" className="btn-ghost" onClick={() => exportCsv.mutate()}>
                <Icon name="download" size={16} /> CSV
              </button>
            </div>
          }>
          {students.isPending ? <Loading /> : students.data?.length ? (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[560px] text-sm">
                <thead><tr className="text-left text-faint"><th className="py-2 font-medium">Name</th><th className="py-2 font-medium">Department</th><th className="py-2 font-medium">Target</th><th className="py-2 font-medium">Score</th><th className="py-2 font-medium">Missing</th></tr></thead>
                <tbody>
                  {students.data.map((s) => (
                    <tr key={s.user_id} className="border-t border-line">
                      <td className="py-2.5 text-ink">{s.name || s.email}</td>
                      <td className="py-2.5 text-muted">{s.department || "–"}</td>
                      <td className="py-2.5 capitalize text-muted">{s.target}</td>
                      <td className={`py-2.5 tabular-nums ${s.score !== null && s.score < 50 ? "text-danger" : "text-ink"}`}>{s.score ?? "–"}</td>
                      <td className="py-2.5 text-faint">{s.missing.join(", ") || "–"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <Empty title="No students to show">Students appear here after they turn on Coordinator access.</Empty>}
          <ErrorNote error={exportCsv.error} />
        </Panel>

        <Announcements />
      </div>
    </>
  );
}

function Announcements() {
  const qc = useQueryClient();
  const list = useQuery({ queryKey: ["announcements"], queryFn: () => api<Announcement[]>("/announcements") });
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const post = useMutation({
    mutationFn: () => api("/announcements", { json: { title, body } }),
    onSuccess: () => {
      setTitle("");
      setBody("");
      void qc.invalidateQueries({ queryKey: ["announcements"] });
    },
  });
  return (
    <Panel title="Announcements">
      <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); post.mutate(); }}>
        <input className="input" placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} aria-label="Announcement title" />
        <textarea className="input min-h-[80px] py-2" placeholder="Message" value={body} onChange={(e) => setBody(e.target.value)} aria-label="Announcement message" />
        <button type="submit" className="btn-primary w-full" disabled={!title || !body || post.isPending}>Post</button>
      </form>
      <ul className="mt-4 space-y-2">
        {list.data?.slice(0, 3).map((a) => <li key={a.id} className="text-sm"><p className="text-ink">{a.title}</p><p className="text-faint">{a.body}</p></li>)}
      </ul>
    </Panel>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  const n = useCountUp(typeof value === "number" ? value : null);
  const decimals = typeof value === "number" && !Number.isInteger(value) ? 1 : 0;
  return (
    <div className="glass glass-hover p-5">
      <p className="eyebrow">{label}</p>
      <p className="mt-2 font-serif text-4xl tabular-nums text-ink">
        {typeof value === "number" ? (n ?? 0).toFixed(decimals) : value}
      </p>
    </div>
  );
}
