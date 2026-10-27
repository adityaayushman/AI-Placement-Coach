import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import Icon from "./Icon";
import { ErrorNote } from "./ui";

/** Small CSV upload control. `describe` turns the API response into a one-line confirmation. */
export default function CsvImport({
  path,
  columns,
  invalidate,
  describe,
}: {
  path: string;
  columns: string;
  invalidate: string[][];
  describe: (result: unknown) => string;
}) {
  const qc = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const upload = useMutation({
    mutationFn: () => {
      const form = new FormData();
      form.append("file", file as File);
      return api<unknown>(path, { form });
    },
    onSuccess: () => {
      setFile(null);
      for (const key of invalidate) void qc.invalidateQueries({ queryKey: key });
    },
  });

  return (
    <div className="space-y-3">
      <p className="text-sm text-muted">CSV columns: <code className="text-ink">{columns}</code></p>
      <div className="flex flex-wrap items-center gap-3">
        <label className="btn-ghost">
          <Icon name="upload" size={16} />
          {file ? file.name : "Choose CSV"}
          <input type="file" accept=".csv,text/csv" className="sr-only"
            onChange={(e) => { upload.reset(); setFile(e.target.files?.[0] ?? null); }} />
        </label>
        <button type="button" className="btn-primary" disabled={!file || upload.isPending} onClick={() => upload.mutate()}>
          {upload.isPending ? "Importing" : "Import"}
        </button>
      </div>
      {upload.isSuccess && <p role="status" className="text-sm text-ok">{describe(upload.data)}</p>}
      <ErrorNote error={upload.error} />
    </div>
  );
}
