import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import ConsentList from "../components/ConsentList";
import Icon from "../components/Icon";
import { ErrorNote, Field, PageHeader, Panel } from "../components/ui";

async function download(format: "json" | "csv") {
  const blob = await api<Blob>(`/me/export?format=${format}`, { raw: true });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `my-placement-data.${format}`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function Privacy() {
  const { logout } = useAuth();
  const [confirm, setConfirm] = useState("");
  const exportData = useMutation({ mutationFn: download });
  const remove = useMutation({
    mutationFn: () => api("/me", { method: "DELETE" }),
    onSuccess: logout,
  });

  return (
    <>
      <PageHeader title="Privacy and data" lede="You decide what we use. You can take a copy of everything or delete it." />
      <div className="grid gap-6 xl:grid-cols-2">
        <Panel title="Permissions" className="xl:row-span-2">
          <ConsentList />
          <p className="mt-4 text-xs text-faint">Turning a permission off stops its use straight away. To remove data already stored, delete your account below.</p>
        </Panel>
        <Panel title="Download your data">
          <p className="text-sm text-muted">Every record we hold about you, including scores, answers and activity.</p>
          <div className="mt-4 flex flex-wrap gap-3">
            <button type="button" className="btn-ghost" onClick={() => exportData.mutate("json")} disabled={exportData.isPending}>
              <Icon name="download" size={16} /> JSON
            </button>
            <button type="button" className="btn-ghost" onClick={() => exportData.mutate("csv")} disabled={exportData.isPending}>
              <Icon name="download" size={16} /> CSV
            </button>
          </div>
          <ErrorNote error={exportData.error} />
        </Panel>
        <Panel title="Delete everything">
          <p className="text-sm text-muted">This removes your account, resumes, recordings, scores and history. It cannot be undone.</p>
          <form className="mt-4 space-y-3" onSubmit={(e) => { e.preventDefault(); remove.mutate(); }}>
            <Field label='Type "delete" to confirm'>
              <input className="input" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
            </Field>
            <button type="submit" disabled={confirm !== "delete" || remove.isPending}
              className="btn border border-[rgba(229,138,122,0.5)] bg-[rgba(229,138,122,0.15)] text-ink hover:bg-[rgba(229,138,122,0.25)]">
              {remove.isPending ? "Deleting" : "Delete my account and data"}
            </button>
            <ErrorNote error={remove.error} />
          </form>
        </Panel>
      </div>
    </>
  );
}
