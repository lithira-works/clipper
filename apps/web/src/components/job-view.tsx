"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ArrowLeft,
  Captions,
  CaptionsOff,
  Check,
  Clock,
  Flame,
  Layers,
  LoaderCircle,
  RotateCcw,
  Timer,
  TriangleAlert,
} from "lucide-react";
import { useJob } from "@/lib/use-job";
import type { Job, Stage } from "@/lib/types";
import { cn, formatTime } from "@/lib/utils";
import { ClipCard, ClipCardSkeleton } from "./clip-card";

const STAGES: { key: Stage; label: string }[] = [
  { key: "downloading", label: "Download" },
  { key: "transcribing", label: "Transcribe" },
  { key: "analyzing", label: "Find moments" },
  { key: "reframing", label: "Track speaker" },
  { key: "rendering", label: "Render" },
];
const ORDER: Stage[] = ["queued", ...STAGES.map((s) => s.key), "done"];

// Fixed grid: same columns for skeletons and real clips, so nothing reflows as clips land.
const GRID = "grid grid-cols-1 gap-5 min-[520px]:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4";

export function JobView({ id }: { id: string }) {
  const { job, error } = useJob(id);

  return (
    <main className="container-page flex-1 py-8 sm:py-10">
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 rounded-lg text-sm font-medium text-ink-soft hover:text-ink"
      >
        <ArrowLeft className="size-4" aria-hidden /> New video
      </Link>

      {error ? (
        <div className="mt-6">
          <ErrorPanel message={error} />
        </div>
      ) : !job ? (
        <LoadingState />
      ) : (
        <>
          <SourceHeader job={job} />
          {job.status === "failed" ? (
            <div className="mt-6">
              <ErrorPanel message={job.error ?? "Processing failed"} />
            </div>
          ) : (
            <>
              {job.status !== "succeeded" && <ProgressPanel job={job} />}
              <ClipsSection job={job} />
            </>
          )}
        </>
      )}
    </main>
  );
}

function SourceHeader({ job }: { job: Job }) {
  const s = job.source;
  const r = job.request;
  return (
    <section className="card mt-5 flex flex-col gap-5 p-4 sm:flex-row sm:items-center sm:p-5">
      <div className="aspect-video w-full shrink-0 overflow-hidden rounded-xl border border-line sm:w-52">
        {s?.thumbnail ? (
          // eslint-disable-next-line @next/next/no-img-element -- remote YouTube thumbnail
          <img src={s.thumbnail} alt="" className="size-full object-cover" />
        ) : (
          <div className="skeleton size-full" />
        )}
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-4">
          <h1
            className="line-clamp-2 wrap-break-word text-xl font-semibold leading-snug tracking-tight sm:text-2xl"
            title={s?.title}
          >
            {s?.title ?? "Fetching video details…"}
          </h1>
          <StatusPill status={job.status} />
        </div>
        <p className="mt-1 truncate text-sm text-muted">{s?.channel ?? r.url}</p>

        <ul className="mt-4 flex flex-wrap gap-2" aria-label="Job settings">
          {s && (
            <li className="chip">
              <Clock className="size-3.5" aria-hidden /> {formatTime(s.duration)}
            </li>
          )}
          {s && (
            <li className="chip">
              <Flame className="size-3.5" aria-hidden />
              {s.has_heatmap ? "Replay heatmap" : "Audio + AI picks"}
            </li>
          )}
          <li className="chip">
            <Layers className="size-3.5" aria-hidden /> {r.max_clips} Shorts
          </li>
          <li className="chip">
            <Timer className="size-3.5" aria-hidden /> {r.min_duration}–{r.max_duration}s
          </li>
          <li className="chip">
            {r.caption_style === "none" ? (
              <>
                <CaptionsOff className="size-3.5" aria-hidden /> No captions
              </>
            ) : (
              <>
                <Captions className="size-3.5" aria-hidden />
                {r.caption_style === "bold" ? "Bold captions" : "Minimal captions"}
              </>
            )}
          </li>
        </ul>
      </div>
    </section>
  );
}

function StatusPill({ status }: { status: Job["status"] }) {
  const map = {
    queued: { label: "Queued", cls: "bg-line text-ink-soft" },
    running: { label: "Processing", cls: "bg-gold-soft text-gold-ink" },
    succeeded: { label: "Ready", cls: "bg-success/10 text-success" },
    failed: { label: "Failed", cls: "bg-danger/10 text-danger" },
  } as const;
  const { label, cls } = map[status];
  return (
    <span className={cn("shrink-0 rounded-full px-3 py-1 text-xs font-semibold", cls)}>
      {status === "running" && (
        <LoaderCircle className="-ml-0.5 mr-1 inline size-3 animate-spin" aria-hidden />
      )}
      {label}
    </span>
  );
}

function ProgressPanel({ job }: { job: Job }) {
  const current = ORDER.indexOf(job.stage);
  const pct = Math.round(job.progress * 100);
  const elapsed = useElapsed(job.created_at);

  return (
    <section className="card mt-5 p-5 sm:p-6" aria-label="Processing progress">
      <div className="flex items-baseline justify-between gap-4">
        <p className="min-w-0 truncate font-medium" aria-live="polite">
          {job.message}
        </p>
        <p className="shrink-0 font-mono text-sm tabular-nums text-ink-soft">
          {pct}% <span className="text-muted">· {formatTime(elapsed)}</span>
        </p>
      </div>

      <div
        className="mt-4 h-2 overflow-hidden rounded-full bg-gold-soft"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={pct}
      >
        <div
          className="h-full rounded-full bg-gold transition-[width] duration-700 ease-out"
          style={{ width: `${Math.max(3, pct)}%` }}
        />
      </div>

      <ol className="mt-6 grid gap-3 sm:grid-cols-5 sm:gap-0">
        {STAGES.map((s, i) => {
          const idx = ORDER.indexOf(s.key);
          const state = idx < current ? "done" : idx === current ? "active" : "todo";
          return (
            <li key={s.key} className="relative flex items-center gap-2.5 sm:flex-col sm:gap-2 sm:text-center">
              {i > 0 && (
                // Connector to the previous step (desktop only).
                <span
                  aria-hidden
                  className={cn(
                    "absolute right-1/2 top-3 hidden h-0.5 w-full -translate-x-3 sm:block",
                    idx <= current ? "bg-ink" : "bg-line",
                  )}
                />
              )}
              <span
                className={cn(
                  "relative z-10 grid size-6 shrink-0 place-items-center rounded-full border-2 bg-surface",
                  state === "done" && "border-ink bg-ink text-paper",
                  state === "active" && "border-ink bg-gold",
                  state === "todo" && "border-line-strong",
                )}
              >
                {state === "done" ? (
                  <Check className="size-3.5" strokeWidth={3} aria-hidden />
                ) : state === "active" ? (
                  <LoaderCircle className="size-3.5 animate-spin" aria-hidden />
                ) : null}
              </span>
              <span
                className={cn(
                  "text-sm",
                  state === "todo" && "text-muted",
                  state === "active" && "font-semibold",
                )}
              >
                {s.label}
              </span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

function ClipsSection({ job }: { job: Job }) {
  const done = job.status === "succeeded";
  const pending = done ? 0 : Math.max(0, job.request.max_clips - job.clips.length);
  if (done && job.clips.length === 0) return null;

  return (
    <section className="mt-10" aria-live="polite" aria-busy={!done}>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="eyebrow">{done ? "Ready to post" : "Rendering"}</p>
          <h2 className="mt-1.5 text-2xl font-semibold tracking-tight">
            {done
              ? `${job.clips.length} Short${job.clips.length === 1 ? "" : "s"}`
              : `${job.clips.length} of ${job.request.max_clips} Shorts`}
          </h2>
        </div>
        {done && (
          <p className="flex items-center gap-1.5 text-sm text-muted">
            <Flame className="size-4 text-gold-strong" aria-hidden /> Sorted by viral score
          </p>
        )}
      </div>

      <div className={cn(GRID, "mt-5")}>
        {job.clips.map((c) => (
          <ClipCard key={c.id} clip={c} />
        ))}
        {Array.from({ length: pending }, (_, i) => (
          <ClipCardSkeleton key={`s${i}`} />
        ))}
      </div>
    </section>
  );
}

function LoadingState() {
  return (
    <div aria-busy className="mt-5">
      <div className="card flex flex-col gap-5 p-4 sm:flex-row sm:items-center sm:p-5">
        <div className="skeleton aspect-video w-full rounded-xl sm:w-52" />
        <div className="flex-1 space-y-3">
          <div className="skeleton h-6 w-3/4 rounded-md" />
          <div className="skeleton h-4 w-1/3 rounded-md" />
          <div className="skeleton h-6 w-1/2 rounded-full" />
        </div>
      </div>
      <div className={cn(GRID, "mt-10")}>
        {Array.from({ length: 4 }, (_, i) => (
          <ClipCardSkeleton key={i} />
        ))}
      </div>
    </div>
  );
}

function ErrorPanel({ message }: { message: string }) {
  return (
    <div role="alert" className="card flex flex-col items-start gap-4 p-6 sm:flex-row sm:p-8">
      <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-danger/10">
        <TriangleAlert className="size-5 text-danger" aria-hidden />
      </span>
      <div className="min-w-0 flex-1">
        <h2 className="text-lg font-semibold">Couldn&apos;t make Shorts from this video</h2>
        <p className="mt-1 text-ink-soft">{message}</p>
        <Link href="/" className="btn-secondary mt-5">
          <RotateCcw className="size-4" aria-hidden /> Try another video
        </Link>
      </div>
    </div>
  );
}

function useElapsed(since: string): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);
  return Math.max(0, (now - new Date(since).getTime()) / 1000);
}
