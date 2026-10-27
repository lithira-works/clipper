"use client";

import { useState } from "react";
import { Check, Copy, Download, Flame } from "lucide-react";
import { api } from "@/lib/api";
import type { Clip } from "@/lib/types";
import { cn, formatTime } from "@/lib/utils";

export function ClipCard({ clip }: { clip: Clip }) {
  const [copied, setCopied] = useState(false);
  const caption = `${clip.title}\n\n${clip.hashtags.map((h) => `#${h}`).join(" ")}`;

  async function copy() {
    await navigator.clipboard.writeText(caption);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }

  return (
    <article className="card flex flex-col overflow-hidden">
      <div className="relative aspect-9/16 bg-ink">
        <video
          src={api.mediaUrl(clip.video_url)}
          poster={api.mediaUrl(clip.thumbnail_url)}
          controls
          playsInline
          preload="metadata"
          className="size-full object-cover"
        />
        <span className="pointer-events-none absolute left-3 top-3 rounded-md bg-paper/95 px-2 py-0.5 font-mono text-xs font-bold text-ink">
          #{clip.rank}
        </span>
        <span
          className={cn(
            "pointer-events-none absolute right-3 top-3 inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-bold text-ink",
            clip.virality_score >= 80 ? "bg-gold" : "bg-paper/95",
          )}
          title="Predicted viral score (0–100)"
        >
          <Flame className="size-3.5" aria-hidden /> {clip.virality_score}
        </span>
      </div>

      <div className="flex flex-1 flex-col p-4">
        <h3 className="line-clamp-2 wrap-break-word font-semibold leading-snug" title={clip.title}>
          {clip.title}
        </h3>
        <p className="mt-1.5 line-clamp-2 text-sm leading-relaxed text-ink-soft" title={clip.reason}>
          {clip.reason}
        </p>
        <p className="mt-3 font-mono text-xs text-muted">
          {formatTime(clip.start)}–{formatTime(clip.end)} · {Math.round(clip.duration)}s
        </p>
        <ul className="mt-2.5 flex flex-wrap gap-1.5">
          {clip.hashtags.map((h) => (
            <li key={h} className="rounded-md bg-gold-soft px-1.5 py-0.5 text-xs font-medium text-gold-ink">
              #{h}
            </li>
          ))}
        </ul>
        <div className="mt-auto flex gap-2 pt-4">
          <a href={api.mediaUrl(clip.video_url)} download={`${clip.id}.mp4`} className="btn-secondary flex-1">
            <Download className="size-4" aria-hidden /> Download
          </a>
          <button
            type="button"
            onClick={copy}
            className="btn-ghost px-3"
            aria-label={copied ? "Copied" : "Copy title and hashtags"}
            title="Copy title and hashtags"
          >
            {copied ? (
              <Check className="size-4 text-success" aria-hidden />
            ) : (
              <Copy className="size-4" aria-hidden />
            )}
          </button>
        </div>
      </div>
    </article>
  );
}

export function ClipCardSkeleton() {
  return (
    <div className="card flex flex-col overflow-hidden" aria-hidden>
      <div className="skeleton aspect-9/16" />
      <div className="space-y-2.5 p-4">
        <div className="skeleton h-4 w-5/6 rounded" />
        <div className="skeleton h-3 w-2/3 rounded" />
        <div className="skeleton mt-4 h-10 w-full rounded-xl" />
      </div>
    </div>
  );
}
