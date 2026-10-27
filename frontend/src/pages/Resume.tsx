import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { ApiError, api } from "../api/client";
import type { Analysis, Job } from "../api/types";
import Icon from "../components/Icon";
import { Empty, ErrorNote, Field, Loading, Meter, PageHeader, Panel, ScoreRing } from "../components/ui";

export default function Resume() {
  const qc = useQueryClient();
  const jobs = useQuery({ queryKey: ["jobs"], queryFn: () => api<Job[]>("/jobs") });
  const latest = useQuery({
    queryKey: ["analysis"],
    queryFn: () => api<Analysis | null>("/resumes/analyses/latest"),
    retry: false,
  });
  const [file, setFile] = useState<File | null>(null);
  const [jdId, setJdId] = useState("");

  const upload = useMutation({
    mutationFn: () => {
      const form = new FormData();
      form.append("file", file as File);
      if (jdId) form.append("jd_id", jdId);
      return api<Analysis>("/resumes", { form });
    },
    onSuccess: (a) => {
      qc.setQueryData(["analysis"], a);
      void qc.invalidateQueries({ queryKey: ["readiness"] });
      void qc.invalidateQueries({ queryKey: ["recs"] });
    },
  });

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (file) upload.mutate();
  };
  const needsConsent = latest.error instanceof ApiError && latest.error.status === 403;
  const analysis = latest.data;
  const jd = jobs.data?.find((j) => j.id === analysis?.jd_id);

  return (
    <>
      <PageHeader title="Resume check" lede="See how a screener reads your resume, and which skills a target role expects that you have not shown yet." />
      {needsConsent && (
        <Panel className="mb-6">
          <p className="text-ink">Resume analysis is switched off.</p>
          <p className="mt-1 text-sm text-muted">Turn on <strong>Resume analysis</strong> on the <Link className="text-amber hover:underline" to="/privacy">Privacy page</Link> to upload.</p>
        </Panel>
      )}

      <div className="stagger grid gap-6 xl:grid-cols-3">
        <Panel title="Upload" eyebrow="PDF, DOCX or TXT, up to 5 MB">
          <form onSubmit={submit} className="space-y-4">
            <label className="flex min-h-[120px] cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-line bg-white/[0.03] px-4 text-center transition-colors duration-200 hover:bg-white/[0.06]">
              <Icon name="upload" size={22} />
              <span className="text-sm text-ink">{file ? file.name : "Choose a file"}</span>
              <input type="file" accept=".pdf,.docx,.txt" className="sr-only" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
            </label>
            <Field label="Compare against" hint="Pick a role to get a skill-gap report.">
              <select className="input" value={jdId} onChange={(e) => setJdId(e.target.value)}>
                <option value="">No role, resume checks only</option>
                {jobs.data?.map((j) => <option key={j.id} value={j.id}>{j.role} · {j.company}</option>)}
              </select>
            </Field>
            <button type="submit" className="btn-primary w-full" disabled={!file || upload.isPending || needsConsent}>
              {upload.isPending ? "Analysing" : "Analyse resume"}
            </button>
            <ErrorNote error={upload.error} />
          </form>
        </Panel>

        <Panel className="xl:col-span-2" title="Report" eyebrow={jd ? `${jd.role} · ${jd.company}` : "Latest analysis"}>
          {latest.isPending ? <Loading /> : !analysis ? (
            <Empty title="No report yet">Upload a resume to see your checks.</Empty>
          ) : (
            <div className="stagger grid gap-6 md:grid-cols-[auto_1fr]">
              <div className="flex flex-col items-center">
                <ScoreRing score={analysis.ats_score} size={140} />
                <p className="mt-2 text-sm text-muted">ATS score</p>
                {analysis.match_scores.overall !== undefined && (
                  <p className="mt-3 text-sm text-muted">Text match <span className="text-ink">{Math.round(analysis.match_scores.overall * 100)}%</span></p>
                )}
              </div>
              <ul className="space-y-4">
                {analysis.ats_report.ats_checks.map((c) => (
                  <li key={c.id}>
                    <Meter label={c.label} value={(c.points / c.max_points) * 100} hint={c.detail} />
                    {c.fix && <p className="mt-1 text-sm text-rose">{c.fix}</p>}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Panel>

        {analysis && (
          <>
            <Panel title="Skill gaps" eyebrow="Ranked by importance for this role" className="xl:col-span-2">
              {analysis.jd_id === null ? (
                <Empty title="No role selected">Pick a role and re-upload to see gaps.</Empty>
              ) : analysis.skill_gaps.length === 0 ? (
                <Empty title="No gaps found">Your resume covers every required skill for this role.</Empty>
              ) : (
                <ol className="stagger space-y-3">
                  {analysis.skill_gaps.map((g, i) => (
                    <li key={g.skill} className="flex gap-4 rounded-2xl border border-line bg-white/[0.03] p-4">
                      <span className="font-serif text-lg tabular-nums text-faint">{i + 1}</span>
                      <div>
                        <p className="capitalize text-ink">{g.skill} <span className="chip ml-2">{g.category}</span></p>
                        <p className="mt-1 text-sm text-muted">{g.reason}</p>
                      </div>
                    </li>
                  ))}
                </ol>
              )}
            </Panel>
            <Panel title="Skills we found">
              <div className="flex flex-wrap gap-2">
                {analysis.skills_found.map((s) => <span key={s} className="chip capitalize text-ink">{s}</span>)}
                {analysis.skills_found.length === 0 && <p className="text-sm text-faint">None detected. Add a Skills section.</p>}
              </div>
              <p className="mt-4 text-xs text-faint">Matching uses {analysis.ats_report.embedder}: a word-overlap model, so synonyms it has not seen can be missed.</p>
            </Panel>
          </>
        )}
      </div>
    </>
  );
}
