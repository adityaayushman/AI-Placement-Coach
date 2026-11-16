import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Empty } from "../components/ui";

import {
  ABLATION,
  ABLATION_SYNTHETIC,
  CALIBRATION,
  FAIRNESS,
  FAIRNESS_SYNTHETIC,
  GENERATED_AT,
  HOLDOUT,
  HOLDOUT_SYNTHETIC,
  KNOWLEDGE_TRACING,
  MODEL_COMPARISON,
  MODEL_COMPARISON_SYNTHETIC,
  REAL_DATASET_LABEL,
  RESUME_MATCH,
  TARGETS,
  TRACKING_GAIN,
  UNRECORDED_REAL_FEATURES,
} from "../data/evaluation";

const tooltipStyle = {
  background: "rgba(33,25,21,0.92)",
  border: "1px solid rgba(244,228,210,0.14)",
  borderRadius: 12,
  color: "#f4ebe1",
};
const axisProps = { stroke: "#9a8a7b", tickLine: false, axisLine: false, fontSize: 11 } as const;
const BARS = ["#a77b8e", "#d6a594", "#e2b062"];

function Chart({ data, xKey, yKey, suffix = "", height = 220 }: {
  data: Record<string, unknown>[];
  xKey: string;
  yKey: string;
  suffix?: string;
  height?: number;
}) {
  return (
    <div style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 4, right: 4, left: -8, bottom: 4 }}>
          <XAxis dataKey={xKey} {...axisProps} interval={0} angle={-12} textAnchor="end" height={48} />
          <YAxis {...axisProps} width={36} tickFormatter={(v: number) => `${Math.round(v * 100)}${suffix}`} />
          <Tooltip
            contentStyle={tooltipStyle}
            formatter={(v: number) => `${(v * 100).toFixed(1)}%`}
          />
          <Bar dataKey={yKey} radius={[6, 6, 0, 0]}>
            {data.map((_, i) => <Cell key={i} fill={BARS[i % BARS.length]} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function SynthChip({ children = "Synthetic data" }: { children?: string }) {
  return <span className="chip">{children}</span>;
}

function Section({ title, synth, children }: { title: string; synth?: string; children: ReactNode }) {
  return (
    <section className="glass glass-hover p-6 sm:p-7">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-serif text-xl text-ink">{title}</h2>
        <SynthChip>{synth ?? "Synthetic data"}</SynthChip>
      </div>
      {children}
    </section>
  );
}

export default function Results() {
  return (
    <div className="min-h-screen px-4 py-10 sm:px-8 lg:px-16">
      <header className="mx-auto mb-10 max-w-5xl">
        <p className="eyebrow">AI Placement Coach</p>
        <h1 className="page-enter mt-2 font-serif text-4xl tracking-tight text-ink">Results &amp; Analysis</h1>
        <p className="mt-3 max-w-2xl text-muted">
          Every number on this page comes from <code className="text-ink">scripts/evaluate.py</code>, which
          regenerates <code className="text-ink">docs/EVALUATION.md</code> from the live code. Each section
          states its real data source &mdash; nothing here is presented as real-pilot evidence unless it is.
        </p>
        <p className="mt-2 text-sm text-faint">Generated {GENERATED_AT} &middot; <Link to="/login" className="text-amber hover:underline">Back to sign in</Link></p>
      </header>

      <div className="stagger mx-auto grid max-w-5xl gap-6">
        <Section title="1. Placement readiness predictor" synth="Real data · not SRM">
          <p className="mb-2 text-sm text-muted">
            Three models compared by 5-fold stratified cross-validation on an 80/20 split of a{" "}
            <strong className="text-ink">real</strong>, third-party dataset ({REAL_DATASET_LABEL},
            10,000 rows). Logistic regression won and was Platt-calibrated.
          </p>
          <p className="mb-4 rounded-xl border border-line bg-white/[0.03] p-3 text-xs text-faint">
            No public SRM KTR placement dataset could be found (checked Kaggle, Hugging Face and
            GitHub) &mdash; see docs/DATA_PLAN.md. This source does not record{" "}
            {UNRECORDED_REAL_FEATURES.join(", ")}; those five features are held at a fixed constant
            rather than guessed, so they carry ~0 signal below.
          </p>
          <Chart data={MODEL_COMPARISON} xKey="model" yKey="cv_roc_auc" />
          <div className="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-4">
            {[
              ["Accuracy", HOLDOUT.accuracy],
              ["F1", HOLDOUT.f1],
              ["ROC-AUC", HOLDOUT.roc_auc],
              ["Brier (lower better)", HOLDOUT.brier],
            ].map(([label, value]) => (
              <div key={label as string} className="rounded-xl border border-line bg-white/[0.03] p-3 text-center">
                <p className="font-serif text-2xl text-ink">{((value as number) * 100).toFixed(1)}%</p>
                <p className="mt-1 text-xs text-faint">{label}</p>
              </div>
            ))}
          </div>
          <p className="mt-4 text-xs text-faint">Hold-out performance, same real-data split.</p>
        </Section>

        <Section title="1b. Synthetic generator (comparison)" synth="Synthetic data">
          <p className="mb-4 text-sm text-muted">
            Kept alongside the real result above, exactly as docs/EVALUATION.md does, so the
            earlier synthetic-only story isn&rsquo;t lost.
          </p>
          <Chart data={MODEL_COMPARISON_SYNTHETIC} xKey="model" yKey="cv_roc_auc" height={180} />
          <div className="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-4">
            {[
              ["Accuracy", HOLDOUT_SYNTHETIC.accuracy],
              ["F1", HOLDOUT_SYNTHETIC.f1],
              ["ROC-AUC", HOLDOUT_SYNTHETIC.roc_auc],
              ["Brier (lower better)", HOLDOUT_SYNTHETIC.brier],
            ].map(([label, value]) => (
              <div key={label as string} className="rounded-xl border border-line bg-white/[0.03] p-3 text-center">
                <p className="font-serif text-xl text-ink">{((value as number) * 100).toFixed(1)}%</p>
                <p className="mt-1 text-xs text-faint">{label}</p>
              </div>
            ))}
          </div>
        </Section>

        <Section title="2. Ablation: marks alone vs full feature set" synth="Real data · not SRM">
          <p className="mb-4 text-sm text-muted">
            Academics-only features (CGPA, backlogs, 10th/12th %) versus the full set, same model,
            same hold-out, on the real dataset. The gap is small here because five of the extra
            features above are held constant &mdash; the real lift comes only from the aptitude
            test and soft-skills columns this source actually records.
          </p>
          <Chart data={ABLATION} xKey="features" yKey="accuracy" />
          <p className="mt-3 text-sm text-ink">
            +{Math.round((ABLATION[1].accuracy - ABLATION[0].accuracy) * 100)} accuracy point(s)
            beyond marks on real data, vs +
            {Math.round((ABLATION_SYNTHETIC[1].accuracy - ABLATION_SYNTHETIC[0].accuracy) * 100)}{" "}
            points on the synthetic generator (chip 1b), which assumes practice signals matter more.
          </p>
        </Section>

        <Section title="3. Calibration &amp; fairness" synth="Real data · not SRM">
          <p className="mb-3 text-sm text-muted">Predicted probability vs observed outcome rate, by confidence bin.</p>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[420px] text-sm">
              <thead><tr className="text-left text-faint"><th className="py-1.5 font-medium">Bin</th><th className="py-1.5 font-medium">n</th><th className="py-1.5 font-medium">Predicted</th><th className="py-1.5 font-medium">Observed</th></tr></thead>
              <tbody>
                {CALIBRATION.map((c) => (
                  <tr key={c.bin} className="border-t border-line">
                    <td className="py-1.5 text-ink">{c.bin}</td>
                    <td className="py-1.5 text-muted">{c.n}</td>
                    <td className="py-1.5 tabular-nums text-muted">{(c.predicted * 100).toFixed(1)}%</td>
                    <td className="py-1.5 tabular-nums text-ink">{(c.observed * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mb-3 mt-6 text-sm text-muted">Fairness by department and gender:</p>
          {FAIRNESS.length === 0 ? (
            <Empty title="No demographic columns in this dataset">
              Fairness can&rsquo;t be checked on real data here. The synthetic generator&rsquo;s
              fairness check (below) exists for exactly this reason &mdash; it has department and
              gender fields.
            </Empty>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[480px] text-sm">
                <thead><tr className="text-left text-faint"><th className="py-1.5 font-medium">Group</th><th className="py-1.5 font-medium">n</th><th className="py-1.5 font-medium">Selection</th><th className="py-1.5 font-medium">TPR</th><th className="py-1.5 font-medium">Accuracy</th></tr></thead>
                <tbody>
                  {FAIRNESS.map((f) => (
                    <tr key={f.group} className="border-t border-line">
                      <td className="py-1.5 text-ink">{f.group}</td>
                      <td className="py-1.5 text-muted">{f.n}</td>
                      <td className="py-1.5 tabular-nums text-muted">{(f.selection_rate * 100).toFixed(1)}%</td>
                      <td className="py-1.5 tabular-nums text-muted">{(f.tpr * 100).toFixed(1)}%</td>
                      <td className="py-1.5 tabular-nums text-ink">{(f.accuracy * 100).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <p className="mb-3 mt-6 text-sm text-muted">
            Synthetic generator&rsquo;s fairness (chip 1b, has department/gender):
          </p>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[480px] text-sm">
              <thead><tr className="text-left text-faint"><th className="py-1.5 font-medium">Group</th><th className="py-1.5 font-medium">n</th><th className="py-1.5 font-medium">Selection</th><th className="py-1.5 font-medium">TPR</th><th className="py-1.5 font-medium">Accuracy</th></tr></thead>
              <tbody>
                {FAIRNESS_SYNTHETIC.map((f) => (
                  <tr key={f.group} className="border-t border-line">
                    <td className="py-1.5 text-ink">{f.group}</td>
                    <td className="py-1.5 text-muted">{f.n}</td>
                    <td className="py-1.5 tabular-nums text-muted">{(f.selection_rate * 100).toFixed(1)}%</td>
                    <td className="py-1.5 tabular-nums text-muted">{(f.tpr * 100).toFixed(1)}%</td>
                    <td className="py-1.5 tabular-nums text-ink">{(f.accuracy * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>

        <Section title="4. Resume &amp; skill-gap matching" synth="4 author-written pairs">
          <p className="mb-3 text-sm text-muted">
            Precision and recall of skill-gap detection on 4 resume/JD pairs the team wrote and
            labelled itself &mdash; a regression check, not a human-annotated evaluation.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[460px] text-sm">
              <thead><tr className="text-left text-faint"><th className="py-1.5 font-medium">Embedder</th><th className="py-1.5 font-medium">Precision</th><th className="py-1.5 font-medium">Recall</th><th className="py-1.5 font-medium">TP / FP / FN</th></tr></thead>
              <tbody>
                {RESUME_MATCH.map((r) => (
                  <tr key={r.embedder} className="border-t border-line">
                    <td className="py-1.5 text-ink">{r.embedder}</td>
                    <td className="py-1.5 tabular-nums text-muted">{(r.precision * 100).toFixed(0)}%</td>
                    <td className="py-1.5 tabular-nums text-muted">{(r.recall * 100).toFixed(0)}%</td>
                    <td className="py-1.5 tabular-nums text-ink">{r.tp} / {r.fp} / {r.fn}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>

        <Section title="5. Knowledge tracing: DKT vs BKT">
          <p className="mb-4 text-sm text-muted">
            Held-out next-answer AUC on synthetic multi-skill sequences (2000 simulated learners).
            A deep model (DKT) did not beat a properly tuned BKT here, so BKT stays the default.
          </p>
          <Chart data={KNOWLEDGE_TRACING} xKey="model" yKey="auc" />
        </Section>

        <Section title="6. Skill-gap tracking gain" synth="Simulated, shares recommender's assumptions">
          <p className="mb-4 text-sm text-muted">
            Recommender vs random topic order vs a fixed syllabus, on simulated learners (400 per
            policy, 30 study sessions). Shows the closed feedback loop works as designed.
          </p>
          <div className="grid gap-6 sm:grid-cols-2">
            <div>
              <p className="mb-2 text-sm text-ink">Product companies</p>
              <Chart data={TRACKING_GAIN.filter((t) => t.company === "Product")} xKey="policy" yKey="gap_closed" height={180} />
            </div>
            <div>
              <p className="mb-2 text-sm text-ink">Service companies</p>
              <Chart data={TRACKING_GAIN.filter((t) => t.company === "Service")} xKey="policy" yKey="gap_closed" height={180} />
            </div>
          </div>
        </Section>

        <Section title="7. Targets vs measured" synth="Not directly comparable">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-sm">
              <thead><tr className="text-left text-faint"><th className="py-1.5 font-medium">Target</th><th className="py-1.5 font-medium">Measured here</th><th className="py-1.5 font-medium">Why not comparable</th></tr></thead>
              <tbody>
                {TARGETS.map((t) => (
                  <tr key={t.target} className="border-t border-line align-top">
                    <td className="py-2 text-ink">{t.target}</td>
                    <td className="py-2 text-muted">{t.measured}</td>
                    <td className="py-2 text-faint">{t.why}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-4 text-sm text-ink">
            Closing this gap needs a real pilot: 200&ndash;300 students, human-rated interview
            answers, and an annotated resume/JD set.
          </p>
        </Section>
      </div>

      <footer className="mx-auto mt-10 max-w-5xl text-center text-sm text-faint">
        <Link to="/login" className="text-amber hover:underline">Back to sign in</Link>
      </footer>
    </div>
  );
}
