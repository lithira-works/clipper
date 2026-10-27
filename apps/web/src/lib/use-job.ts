"use client";

import { useEffect, useState } from "react";
import { api } from "./api";
import type { Job } from "./types";

/** Live job state: Server-Sent Events first, polling fallback if the stream drops. */
export function useJob(id: string) {
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let stopped = false;
    let poll: ReturnType<typeof setInterval> | undefined;
    const done = (j: Job) => j.status === "succeeded" || j.status === "failed";

    const startPolling = () => {
      if (poll) return;
      poll = setInterval(async () => {
        try {
          const j = await api.getJob(id);
          if (stopped) return;
          setJob(j);
          if (done(j)) clearInterval(poll);
        } catch (e) {
          setError(e instanceof Error ? e.message : "Could not load job");
          clearInterval(poll);
        }
      }, 2500);
    };

    const es = new EventSource(api.eventsUrl(id));
    es.addEventListener("job", (ev) => {
      const j = JSON.parse((ev as MessageEvent<string>).data) as Job;
      setJob(j);
      if (done(j)) es.close();
    });
    es.onerror = () => {
      es.close();
      if (!stopped) startPolling();
    };

    return () => {
      stopped = true;
      es.close();
      if (poll) clearInterval(poll);
    };
  }, [id]);

  return { job, error };
}
