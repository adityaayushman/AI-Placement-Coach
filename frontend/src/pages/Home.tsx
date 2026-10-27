const modules = [
  ["Readiness", "How likely you are to be placed, and what drives it."],
  ["Resume", "How your resume reads to a screener, and which skills it misses."],
  ["Interview", "Practice answers out loud and get specific feedback."],
  ["Plan", "The next topic worth your time, and why."],
];

export default function Home() {
  return (
    <>
      <h1 className="max-w-xl font-serif text-4xl leading-tight tracking-tight sm:text-5xl">
        Know where you stand. Know what to do next.
      </h1>
      <p className="mt-6 max-w-lg text-muted">
        Placement Coach brings your academics, resume, practice and interviews into one honest
        picture of your readiness, and updates it as you improve.
      </p>

      <section aria-labelledby="score" className="mt-16 border-t border-line pt-8">
        <h2 id="score" className="text-sm text-muted">
          Your readiness score
        </h2>
        <p className="mt-2 font-serif text-6xl text-muted/50" aria-label="No score yet">
          —
        </p>
        <p className="mt-2 text-sm text-muted">
          Nothing to show yet. Sign-in and profile setup arrive in the next phase.
        </p>
      </section>

      <section aria-labelledby="parts" className="mt-16">
        <h2 id="parts" className="text-sm text-muted">
          What it will cover
        </h2>
        <ol className="mt-4 divide-y divide-line border-y border-line">
          {modules.map(([name, blurb], i) => (
            <li key={name} className="flex items-baseline gap-6 py-4">
              <span className="w-5 text-sm tabular-nums text-muted">{i + 1}</span>
              <span className="w-24 font-serif text-lg">{name}</span>
              <span className="flex-1 text-sm text-muted">{blurb}</span>
            </li>
          ))}
        </ol>
      </section>
    </>
  );
}
