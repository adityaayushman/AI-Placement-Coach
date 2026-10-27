import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type FormEvent } from "react";

import { api } from "../api/client";
import type { Profile as ProfileT } from "../api/types";
import CsvImport from "../components/CsvImport";
import Icon from "../components/Icon";
import { ErrorNote, Field, Loading, PageHeader, Panel } from "../components/ui";

type Row = Record<string, unknown> & { id: number };

const num = (v: string): number | null => (v === "" ? null : Number(v));

export default function Profile() {
  const qc = useQueryClient();
  const profile = useQuery({ queryKey: ["profile"], queryFn: () => api<ProfileT>("/me/profile") });
  const [form, setForm] = useState<ProfileT | null>(null);
  const [saved, setSaved] = useState(false);
  useEffect(() => {
    if (profile.data) setForm(profile.data);
  }, [profile.data]);

  const save = useMutation({
    mutationFn: (p: ProfileT) => api<ProfileT>("/me/profile", { method: "PUT", json: p }),
    onSuccess: (d) => {
      qc.setQueryData(["profile"], d);
      void qc.invalidateQueries({ queryKey: ["readiness"] });
      setSaved(true);
    },
  });

  if (profile.isPending || !form) return <Loading />;
  const set = <K extends keyof ProfileT>(k: K, v: ProfileT[K]) => {
    setSaved(false);
    setForm({ ...form, [k]: v });
  };
  const submit = (e: FormEvent) => {
    e.preventDefault();
    save.mutate(form);
  };

  return (
    <>
      <PageHeader title="Profile" lede="Your score updates each time you save or add an entry." />
      <div className="grid gap-6 xl:grid-cols-2">
        <Panel title="Academics and target" className="xl:row-span-2">
          <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2">
            <Field label="Department">
              <input className="input" value={form.department} onChange={(e) => set("department", e.target.value)} placeholder="CSE" />
            </Field>
            <Field label="Graduation year">
              <input className="input" type="number" value={form.graduation_year ?? ""} onChange={(e) => set("graduation_year", num(e.target.value))} />
            </Field>
            <Field label="CGPA (out of 10)">
              <input className="input" type="number" step="0.01" min={0} max={10} value={form.cgpa ?? ""} onChange={(e) => set("cgpa", num(e.target.value))} />
            </Field>
            <Field label="Active backlogs">
              <input className="input" type="number" min={0} value={form.backlogs} onChange={(e) => set("backlogs", Number(e.target.value))} />
            </Field>
            <Field label="10th %">
              <input className="input" type="number" step="0.1" value={form.tenth_pct ?? ""} onChange={(e) => set("tenth_pct", num(e.target.value))} />
            </Field>
            <Field label="12th %">
              <input className="input" type="number" step="0.1" value={form.twelfth_pct ?? ""} onChange={(e) => set("twelfth_pct", num(e.target.value))} />
            </Field>
            <Field label="Internships">
              <input className="input" type="number" min={0} value={form.internships} onChange={(e) => set("internships", Number(e.target.value))} />
            </Field>
            <Field label="Target companies">
              <select className="input" value={form.target_company_type} onChange={(e) => set("target_company_type", e.target.value as ProfileT["target_company_type"])}>
                <option value="product">Product companies</option>
                <option value="service">Service companies</option>
              </select>
            </Field>
            <Field label="Target role">
              <input className="input" value={form.target_role} onChange={(e) => set("target_role", e.target.value)} />
            </Field>
            <Field label="Gender (optional)" hint="Used only for fairness checks on the model.">
              <input className="input" value={form.gender ?? ""} onChange={(e) => set("gender", e.target.value || null)} />
            </Field>
            <div className="flex items-center gap-4 sm:col-span-2">
              <button type="submit" className="btn-primary" disabled={save.isPending}>{save.isPending ? "Saving" : "Save profile"}</button>
              {saved && <span role="status" className="text-sm text-ok">Saved. Your score is updated.</span>}
            </div>
            <div className="sm:col-span-2"><ErrorNote error={save.error} /></div>
          </form>
        </Panel>

        <Panel title="Semester results" eyebrow="Import from your marksheet">
          <CsvImport path="/me/academics/import" columns="term,gpa,backlogs"
            invalidate={[["profile"], ["readiness"]]}
            describe={(r) => `Imported ${(r as unknown[]).length} terms. CGPA and backlogs are updated.`} />
        </Panel>
        <EntryList title="Coding practice" path="/me/coding"
          fields={[{ key: "platform", label: "Platform", placeholder: "LeetCode" }, { key: "problems_solved", label: "Problems solved", type: "number" }, { key: "contest_rating", label: "Rating", type: "number" }]}
          render={(r) => `${r.platform}: ${r.problems_solved} solved${r.contest_rating ? `, rating ${r.contest_rating}` : ""}`} />
        <EntryList title="Projects" path="/me/projects"
          fields={[{ key: "title", label: "Title" }, { key: "complexity", label: "Complexity 1-3", type: "number" }]}
          render={(r) => `${r.title} (complexity ${r.complexity})`} />
        <EntryList title="Certifications" path="/me/certifications"
          fields={[{ key: "name", label: "Name" }, { key: "issuer", label: "Issuer" }]}
          render={(r) => `${r.name}${r.issuer ? `, ${r.issuer}` : ""}`} />
      </div>
    </>
  );
}

interface FieldSpec {
  key: string;
  label: string;
  type?: string;
  placeholder?: string;
}

function EntryList({ title, path, fields, render }: { title: string; path: string; fields: FieldSpec[]; render: (r: Row) => string }) {
  const qc = useQueryClient();
  const rows = useQuery({ queryKey: [path], queryFn: () => api<Row[]>(path) });
  const [draft, setDraft] = useState<Record<string, string>>({});
  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: [path] });
    void qc.invalidateQueries({ queryKey: ["readiness"] });
  };
  const add = useMutation({
    mutationFn: () => {
      const body: Record<string, unknown> = {};
      for (const f of fields) {
        const v = draft[f.key] ?? "";
        if (v !== "") body[f.key] = f.type === "number" ? Number(v) : v;
      }
      return api(path, { json: body });
    },
    onSuccess: () => {
      setDraft({});
      invalidate();
    },
  });
  const remove = useMutation({ mutationFn: (id: number) => api(`${path}/${id}`, { method: "DELETE" }), onSuccess: invalidate });

  return (
    <Panel title={title}>
      <form className="flex flex-wrap items-end gap-3" onSubmit={(e) => { e.preventDefault(); add.mutate(); }}>
        {fields.map((f) => (
          <div key={f.key} className="min-w-[8rem] flex-1">
            <Field label={f.label}>
              <input className="input" type={f.type ?? "text"} placeholder={f.placeholder} value={draft[f.key] ?? ""}
                onChange={(e) => setDraft({ ...draft, [f.key]: e.target.value })} />
            </Field>
          </div>
        ))}
        <button type="submit" className="btn-ghost" disabled={add.isPending}>Add</button>
      </form>
      <ErrorNote error={add.error} />
      <ul className="mt-4 divide-y divide-[var(--line)]">
        {rows.data?.map((r) => (
          <li key={r.id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
            <span className="text-ink">{render(r)}</span>
            <button type="button" className="cursor-pointer rounded-full p-2 text-faint hover:bg-white/5 hover:text-ink" aria-label="Remove entry" onClick={() => remove.mutate(r.id)}>
              <Icon name="x" size={16} />
            </button>
          </li>
        ))}
        {rows.data?.length === 0 && <li className="py-2.5 text-sm text-faint">Nothing added yet.</li>}
      </ul>
    </Panel>
  );
}
