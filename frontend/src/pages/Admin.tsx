import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import type { Job } from "../api/types";
import { ErrorNote, Field, Loading, PageHeader, Panel } from "../components/ui";

interface AuditRow { id: number; actor_id: number | null; action: string; target: string; created_at: string }
interface ModelRow { version: string; is_active: boolean; data_hash: string; metrics: { holdout?: Record<string, number>; source?: string }; created_at: string }

export default function Admin() {
  const qc = useQueryClient();
  const jobs = useQuery({ queryKey: ["jobs"], queryFn: () => api<Job[]>("/jobs") });
  const audit = useQuery({ queryKey: ["audit"], queryFn: () => api<AuditRow[]>("/admin/audit?limit=50") });
  const models = useQuery({ queryKey: ["models"], queryFn: () => api<ModelRow[]>("/admin/models") });
  const retrain = useMutation({
    mutationFn: () => api<{ version: string }>("/admin/models/retrain", { method: "POST" }),
    onSuccess: () => void qc.invalidateQueries({ queryKey: ["models"] }),
  });
  const [staff, setStaff] = useState({ email: "", password: "", full_name: "", role: "coordinator" });
  const createStaff = useMutation({ mutationFn: () => api("/admin/users", { json: staff }) });
  const [jd, setJd] = useState({ company: "", role: "", type: "product", text: "", skills: "" });
  const addJd = useMutation({
    mutationFn: () => api("/jobs", {
      json: {
        company: jd.company, role: jd.role, type: jd.type, text: jd.text,
        required_skills: jd.skills.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean).map((skill) => ({ skill, weight: 1 })),
      },
    }),
    onSuccess: () => {
      setJd({ company: "", role: "", type: "product", text: "", skills: "" });
      void qc.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  return (
    <>
      <PageHeader title="Administration" />
      <div className="grid gap-6 xl:grid-cols-2">
        <Panel title="Readiness models" action={<button type="button" className="btn-ghost" onClick={() => retrain.mutate()} disabled={retrain.isPending}>{retrain.isPending ? "Training" : "Retrain"}</button>}>
          {models.isPending ? <Loading /> : (
            <ul className="space-y-3 text-sm">
              {models.data?.map((m) => (
                <li key={m.version} className="rounded-xl border border-line p-3">
                  <p className="break-all text-ink">{m.version} {m.is_active && <span className="chip ml-1">Active</span>}</p>
                  <p className="mt-1 text-faint">Source {m.metrics.source}. Hold-out AUC {m.metrics.holdout?.roc_auc ?? "–"}, accuracy {m.metrics.holdout?.accuracy ?? "–"}.</p>
                </li>
              ))}
              {models.data?.length === 0 && <li className="text-faint">The bootstrap model is in use. Retrain to register a version here.</li>}
            </ul>
          )}
          <ErrorNote error={retrain.error} />
        </Panel>

        <Panel title="Create staff account">
          <form className="grid gap-3 sm:grid-cols-2" onSubmit={(e) => { e.preventDefault(); createStaff.mutate(); }}>
            <Field label="Email"><input className="input" type="email" value={staff.email} onChange={(e) => setStaff({ ...staff, email: e.target.value })} /></Field>
            <Field label="Name"><input className="input" value={staff.full_name} onChange={(e) => setStaff({ ...staff, full_name: e.target.value })} /></Field>
            <Field label="Temporary password"><input className="input" type="password" value={staff.password} onChange={(e) => setStaff({ ...staff, password: e.target.value })} /></Field>
            <Field label="Role">
              <select className="input" value={staff.role} onChange={(e) => setStaff({ ...staff, role: e.target.value })}>
                <option value="coordinator">Coordinator</option><option value="admin">Admin</option>
              </select>
            </Field>
            <div className="sm:col-span-2 flex items-center gap-3">
              <button type="submit" className="btn-primary" disabled={createStaff.isPending}>Create account</button>
              {createStaff.isSuccess && <span role="status" className="text-sm text-ok">Account created.</span>}
            </div>
            <div className="sm:col-span-2"><ErrorNote error={createStaff.error} /></div>
          </form>
        </Panel>

        <Panel title="Job descriptions">
          <form className="grid gap-3" onSubmit={(e) => { e.preventDefault(); addJd.mutate(); }}>
            <div className="grid gap-3 sm:grid-cols-3">
              <Field label="Company"><input className="input" value={jd.company} onChange={(e) => setJd({ ...jd, company: e.target.value })} /></Field>
              <Field label="Role"><input className="input" value={jd.role} onChange={(e) => setJd({ ...jd, role: e.target.value })} /></Field>
              <Field label="Type">
                <select className="input" value={jd.type} onChange={(e) => setJd({ ...jd, type: e.target.value })}><option value="product">Product</option><option value="service">Service</option></select>
              </Field>
            </div>
            <Field label="Description"><textarea className="input min-h-[90px] py-2" value={jd.text} onChange={(e) => setJd({ ...jd, text: e.target.value })} /></Field>
            <Field label="Required skills" hint="Comma separated, using taxonomy names such as python, sql, system design.">
              <input className="input" value={jd.skills} onChange={(e) => setJd({ ...jd, skills: e.target.value })} />
            </Field>
            <button type="submit" className="btn-primary justify-self-start" disabled={!jd.company || !jd.role || !jd.text}>Add job description</button>
            <ErrorNote error={addJd.error} />
          </form>
          <ul className="mt-4 divide-y divide-[var(--line)] text-sm">
            {jobs.data?.map((j) => <li key={j.id} className="py-2"><span className="text-ink">{j.role}</span> <span className="text-faint">· {j.company} · {j.required_skills.length} skills</span></li>)}
          </ul>
        </Panel>

        <Panel title="Audit log">
          {audit.isPending ? <Loading /> : (
            <ul className="max-h-[420px] space-y-1 overflow-y-auto text-sm">
              {audit.data?.map((a) => (
                <li key={a.id} className="flex justify-between gap-4 border-b border-line py-2">
                  <span className="text-ink">{a.action.replace(/_/g, " ")} <span className="text-faint">{a.target}</span></span>
                  <span className="shrink-0 tabular-nums text-faint">{new Date(a.created_at).toLocaleString()}</span>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>
    </>
  );
}
