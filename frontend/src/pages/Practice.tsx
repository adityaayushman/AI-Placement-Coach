import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import type { AssessmentSummary, Attempt, Question } from "../api/types";
import { Empty, ErrorNote, Loading, PageHeader, Panel } from "../components/ui";

export default function Practice() {
  const list = useQuery({ queryKey: ["assessments"], queryFn: () => api<AssessmentSummary[]>("/assessments") });
  const [active, setActive] = useState<number | null>(null);

  return (
    <>
      <PageHeader title="Practice" lede="Short quizzes. Each answer updates your skill mastery and your plan." />
      <div className="grid gap-6 lg:grid-cols-[18rem_1fr]">
        <Panel title="Quizzes">
          {list.isPending ? <Loading /> : (
            <ul className="space-y-1">
              {list.data?.map((a) => (
                <li key={a.id}>
                  <button type="button" onClick={() => setActive(a.id)}
                    className={`flex min-h-[44px] w-full cursor-pointer items-center rounded-xl px-3 text-left text-sm transition-colors duration-200 ${
                      active === a.id ? "bg-white/10 text-ink" : "text-muted hover:bg-white/5 hover:text-ink"}`}>
                    {a.title}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Panel>
        {active ? <Quiz key={active} id={active} /> : (
          <Panel><Empty title="Pick a quiz">Four questions each. Takes about two minutes.</Empty></Panel>
        )}
      </div>
    </>
  );
}

function Quiz({ id }: { id: number }) {
  const qc = useQueryClient();
  const detail = useQuery({
    queryKey: ["assessment", id],
    queryFn: () => api<{ id: number; title: string; questions: Question[] }>(`/assessments/${id}`),
  });
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const submit = useMutation({
    mutationFn: () => api<Attempt>(`/assessments/${id}/attempts`, { json: { answers } }),
    onSuccess: () => {
      for (const k of ["mastery", "recs", "readiness"]) void qc.invalidateQueries({ queryKey: [k] });
    },
  });

  if (detail.isPending) return <Panel><Loading /></Panel>;
  if (detail.isError) return <Panel><ErrorNote error={detail.error} /></Panel>;
  const result = submit.data;
  const qs = detail.data.questions;

  return (
    <Panel title={detail.data.title} eyebrow={result ? `Score ${result.score}%` : `${Object.keys(answers).length} of ${qs.length} answered`}>
      <ol className="space-y-6">
        {qs.map((q, i) => {
          const verdict = result?.correct[String(q.id)];
          return (
            <li key={q.id}>
              <fieldset>
                <legend className="text-ink"><span className="mr-2 text-faint">{i + 1}.</span>{q.prompt}</legend>
                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  {q.options.map((opt, oi) => {
                    const chosen = answers[q.id] === oi;
                    return (
                      <label key={oi}
                        className={`flex min-h-[44px] cursor-pointer items-center gap-3 rounded-xl border px-4 text-sm transition-colors duration-200 ${
                          chosen ? "border-amber bg-[rgba(226,176,98,0.12)] text-ink" : "border-line text-muted hover:bg-white/5"}`}>
                        <input type="radio" name={`q${q.id}`} className="accent-[var(--amber)]" checked={chosen} disabled={Boolean(result)}
                          onChange={() => setAnswers({ ...answers, [q.id]: oi })} />
                        {opt}
                      </label>
                    );
                  })}
                </div>
                {verdict !== undefined && (
                  <p className={`mt-2 text-sm ${verdict ? "text-ok" : "text-danger"}`}>{verdict ? "Correct" : "Not quite"}</p>
                )}
              </fieldset>
            </li>
          );
        })}
      </ol>
      <div className="mt-6 flex items-center gap-3">
        {result ? (
          <button type="button" className="btn-ghost" onClick={() => { submit.reset(); setAnswers({}); }}>Try again</button>
        ) : (
          <button type="button" className="btn-primary" disabled={Object.keys(answers).length < qs.length || submit.isPending}
            onClick={() => submit.mutate()}>
            {submit.isPending ? "Checking" : "Submit answers"}
          </button>
        )}
        <ErrorNote error={submit.error} />
      </div>
    </Panel>
  );
}
