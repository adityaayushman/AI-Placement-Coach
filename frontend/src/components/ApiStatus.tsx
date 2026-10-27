import { useQuery } from "@tanstack/react-query";

import { getHealth } from "../api/client";

export default function ApiStatus() {
  const { data, isPending, isError } = useQuery({ queryKey: ["health"], queryFn: getHealth });
  const ok = !isPending && !isError && data.status === "ok";
  const label = isPending ? "Checking service" : ok ? "Service online" : "Service unreachable";

  return (
    <p role="status" className="flex items-center gap-2">
      <span
        aria-hidden="true"
        className={`h-1.5 w-1.5 rounded-full ${ok ? "bg-accent" : "bg-muted/50"}`}
      />
      {label}
    </p>
  );
}
