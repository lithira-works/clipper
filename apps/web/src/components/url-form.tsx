"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { ArrowRight, Link2, LoaderCircle, Minus, Plus, TriangleAlert } from "lucide-react";
import { api } from "@/lib/api";
import type { CaptionStyle } from "@/lib/types";
import { cn } from "@/lib/utils";

const YT_RE =
  /^https?:\/\/(www\.|m\.|music\.)?(youtube\.com\/(watch\?v=|shorts\/|live\/|embed\/)|youtu\.be\/)[\w-]{11}/;

// Classic Shorts sweet spot is 20–45s; "Long" stays within YouTube's 60s comfort zone.
const LENGTHS = [
  { label: "Short", hint: "15–30s", min: 15, max: 30 },
  { label: "Medium", hint: "30–45s", min: 30, max: 45 },
  { label: "Long", hint: "45–60s", min: 45, max: 60 },
] as const;

const CAPTION_STYLES: { value: Exclude<CaptionStyle, "none">; label: string }[] = [
  { value: "bold", label: "Bold karaoke" },
  { value: "minimal", label: "Minimal" },
];

const MIN_CLIPS = 1;
const MAX_CLIPS = 12;

export function UrlForm() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [clips, setClips] = useState(5);
  const [length, setLength] = useState(0);
  const [captionsOn, setCaptionsOn] = useState(true);
  const [style, setStyle] = useState<Exclude<CaptionStyle, "none">>("bold");
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const trimmed = url.trim();
    if (!YT_RE.test(trimmed)) {
      setError("Paste a YouTube video link, e.g. https://youtu.be/abc123XYZ_0");
      return;
    }
    const { min, max } = LENGTHS[length];
    startTransition(async () => {
      try {
        const job = await api.createJob({
          url: trimmed,
          max_clips: clips,
          min_duration: min,
          max_duration: max,
          caption_style: captionsOn ? style : "none",
        });
        router.push(`/jobs/${job.id}`);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Something went wrong");
      }
    });
  }

  return (
    <form onSubmit={submit} className="w-full" aria-describedby={error ? "url-error" : undefined}>
      <div className="flex flex-col gap-3 rounded-2xl border-2 border-ink bg-surface p-2 shadow-(--shadow-press) sm:flex-row sm:items-center">
        <label className="flex flex-1 items-center gap-3 px-3">
          <Link2 className="size-5 shrink-0 text-muted" aria-hidden />
          <span className="sr-only">YouTube video URL</span>
          <input
            type="url"
            inputMode="url"
            required
            autoComplete="off"
            spellCheck={false}
            placeholder="Paste a YouTube link…"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="h-12 w-full bg-transparent text-base outline-none placeholder:text-muted"
          />
        </label>
        <button type="submit" className="btn-primary h-12 shadow-none" disabled={pending}>
          {pending ? (
            <LoaderCircle className="size-5 animate-spin" aria-hidden />
          ) : (
            <>
              Generate Shorts <ArrowRight className="size-4" aria-hidden />
            </>
          )}
        </button>
      </div>

      {error && (
        <p id="url-error" role="alert" className="mt-3 flex items-center gap-2 text-sm text-danger">
          <TriangleAlert className="size-4" aria-hidden /> {error}
        </p>
      )}

      <div className="card mt-4 grid gap-6 p-5 sm:grid-cols-3">
        <fieldset>
          <legend className="eyebrow mb-2">Captions</legend>
          <div className="flex items-center gap-3">
            <button
              type="button"
              role="switch"
              aria-checked={captionsOn}
              aria-label="Captions"
              onClick={() => setCaptionsOn((v) => !v)}
              className={cn(
                "relative h-7 w-12 shrink-0 rounded-full border-2 border-ink transition-colors",
                captionsOn ? "bg-gold" : "bg-line",
              )}
            >
              <span
                className={cn(
                  "absolute top-0.5 size-5 rounded-full bg-ink transition-[left] duration-150",
                  captionsOn ? "left-[1.375rem]" : "left-0.5",
                )}
              />
            </button>
            <span className="text-sm font-semibold">{captionsOn ? "On" : "Off"}</span>
          </div>
          {captionsOn && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {CAPTION_STYLES.map((o) => (
                <Chip key={o.value} active={o.value === style} onClick={() => setStyle(o.value)}>
                  {o.label}
                </Chip>
              ))}
            </div>
          )}
        </fieldset>

        <fieldset>
          <legend className="eyebrow mb-2">Short length</legend>
          <div className="flex flex-wrap gap-1.5">
            {LENGTHS.map((l, i) => (
              <Chip key={l.label} active={i === length} onClick={() => setLength(i)}>
                {l.label} <span className="font-mono text-xs opacity-70">{l.hint}</span>
              </Chip>
            ))}
          </div>
        </fieldset>

        <fieldset>
          <legend className="eyebrow mb-2">Number of Shorts</legend>
          <div className="inline-flex items-center rounded-xl border-2 border-ink bg-surface">
            <button
              type="button"
              aria-label="Fewer Shorts"
              disabled={clips <= MIN_CLIPS}
              onClick={() => setClips((n) => Math.max(MIN_CLIPS, n - 1))}
              className="grid size-10 place-items-center disabled:opacity-30"
            >
              <Minus className="size-4" aria-hidden />
            </button>
            <output aria-live="polite" className="w-10 text-center font-mono text-lg font-semibold">
              {clips}
            </output>
            <button
              type="button"
              aria-label="More Shorts"
              disabled={clips >= MAX_CLIPS}
              onClick={() => setClips((n) => Math.min(MAX_CLIPS, n + 1))}
              className="grid size-10 place-items-center disabled:opacity-30"
            >
              <Plus className="size-4" aria-hidden />
            </button>
          </div>
          <p className="mt-2 text-xs text-muted">Up to {MAX_CLIPS}. Fewer is faster.</p>
        </fieldset>
      </div>
    </form>
  );
}

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm transition-colors",
        active
          ? "border-ink bg-gold font-semibold text-ink"
          : "border-line-strong bg-surface text-ink-soft hover:border-ink",
      )}
    >
      {children}
    </button>
  );
}
