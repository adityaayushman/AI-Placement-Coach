import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";
import type { Consent } from "../api/types";
import { ErrorNote, Loading } from "./ui";

const TITLES: Record<string, string> = {
  resume: "Resume analysis",
  interview_recording: "Interview audio",
  face_analysis: "Camera signals",
  analytics: "Activity history",
  coordinator_visibility: "Coordinator access",
};

export default function ConsentList() {
  const qc = useQueryClient();
  const consents = useQuery({ queryKey: ["consents"], queryFn: () => api<Consent[]>("/consents") });
  const update = useMutation({
    mutationFn: (c: { scope: string; granted: boolean }) =>
      api<Consent[]>("/consents", { method: "PUT", json: [c] }),
    onSuccess: (data) => qc.setQueryData(["consents"], data),
  });

  if (consents.isPending) return <Loading />;
  if (consents.isError) return <ErrorNote error={consents.error} />;

  return (
    <ul className="divide-y divide-[var(--line)]">
      {consents.data.map((c) => (
        <li key={c.scope} className="flex items-center justify-between gap-6 py-4">
          <div>
            <p className="text-ink">{TITLES[c.scope] ?? c.scope}</p>
            <p className="text-sm text-muted">{c.description}</p>
          </div>
          <button
            type="button"
            role="switch"
            aria-checked={c.granted}
            aria-label={TITLES[c.scope] ?? c.scope}
            disabled={update.isPending}
            onClick={() => update.mutate({ scope: c.scope, granted: !c.granted })}
            className={`relative h-7 w-12 shrink-0 cursor-pointer rounded-full border border-line transition-colors duration-200 ${
              c.granted ? "bg-[rgba(226,176,98,0.55)]" : "bg-white/5"
            }`}
          >
            <span
              className={`absolute left-[2px] top-[2px] h-[22px] w-[22px] rounded-full bg-ink transition-transform duration-200 ${
                c.granted ? "translate-x-[20px]" : "translate-x-0"
              }`}
            />
          </button>
        </li>
      ))}
      {update.isError && <ErrorNote error={update.error} />}
    </ul>
  );
}
