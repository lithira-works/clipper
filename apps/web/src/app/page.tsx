import {
  AudioLines,
  Captions,
  Crop,
  Download,
  Flame,
  Link2,
  MonitorSmartphone,
  ScanFace,
  Sparkles,
  Volume2,
  Zap,
} from "lucide-react";
import { PhonePreview } from "@/components/phone-preview";
import { UrlForm } from "@/components/url-form";

const STEPS = [
  {
    icon: Link2,
    title: "Paste a link",
    body: "Any public YouTube video: podcasts, streams, interviews, talks, up to 3 hours.",
  },
  {
    icon: Sparkles,
    title: "AI finds the viral moments",
    body: "Replay heatmap, audio peaks and Claude's editorial judgment pick the clips with the strongest hook and payoff.",
  },
  {
    icon: Download,
    title: "Download your Shorts",
    body: "1080×1920, speaker-tracked, captioned and loudness-normalized. Ready to upload.",
  },
];

const FEATURES = [
  { icon: Flame, title: "Most-replayed detection", body: "Uses YouTube's replay heatmap, the moments real viewers rewatch." },
  { icon: Sparkles, title: "Claude-ranked virality", body: "Scores hook, payoff, emotion and clarity, then writes the title and hook." },
  { icon: ScanFace, title: "Speaker tracking", body: "Face detection keeps the speaker centred in the 9:16 frame." },
  { icon: Captions, title: "Animated captions", body: "Word-by-word captions with the active word popping in gold." },
  { icon: AudioLines, title: "Word-level transcript", body: "Every word is timestamped, so cuts never land mid-sentence." },
  { icon: Volume2, title: "Platform-ready audio", body: "Normalized to −14 LUFS, the loudness YouTube targets." },
  { icon: Crop, title: "Smart fallback layout", body: "No face? The video sits over a blurred fill, nothing cropped." },
];

const HIGHLIGHTS = [
  { icon: MonitorSmartphone, label: "1080×1920 MP4" },
  { icon: Captions, label: "Auto captions" },
  { icon: Zap, label: "Ready in minutes" },
];

export default function Home() {
  return (
    <main>
      <section id="start" className="container-page grid scroll-mt-20 items-center gap-12 pb-16 pt-10 sm:pt-14 lg:grid-cols-[1.2fr_1fr] lg:gap-16 lg:pb-24 lg:pt-20">
        <div className="min-w-0">
          <p className="eyebrow">YouTube → Shorts, automatically</p>
          <h1 className="mt-4 text-4xl font-semibold leading-[1.04] tracking-tight text-balance min-[400px]:text-5xl sm:text-6xl">
            Turn long videos into{" "}
            <span className="relative whitespace-nowrap">
              <span className="relative z-10">viral Shorts</span>
              <span className="absolute inset-x-0 bottom-1 h-3.5 bg-gold/70 sm:h-5" aria-hidden />
            </span>
            .
          </h1>
          <p className="mt-5 max-w-xl text-lg leading-relaxed text-ink-soft">
            Paste a YouTube link. Clipper finds the most replayed, most shareable moments and
            delivers vertical, captioned Shorts in minutes.
          </p>
          <div className="mt-8">
            <UrlForm />
          </div>
          <ul className="mt-5 flex flex-wrap gap-x-5 gap-y-2 text-sm text-ink-soft">
            {HIGHLIGHTS.map((h) => (
              <li key={h.label} className="flex items-center gap-1.5">
                <h.icon className="size-4 text-gold-ink" aria-hidden /> {h.label}
              </li>
            ))}
          </ul>
        </div>
        <PhonePreview />
      </section>

      <section id="how" className="scroll-mt-16 border-y border-line bg-surface">
        <div className="container-page py-20 sm:py-24">
          <p className="eyebrow">How it works</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">Three steps. No editing.</h2>
          <ol className="mt-10 grid gap-5 md:grid-cols-3">
            {STEPS.map((s, i) => (
              <li key={s.title} className="rounded-card border border-line bg-paper p-6 sm:p-7">
                <div className="flex items-center justify-between">
                  <span className="grid size-11 place-items-center rounded-xl border-2 border-ink bg-gold">
                    <s.icon className="size-5" strokeWidth={2} aria-hidden />
                  </span>
                  <span className="font-mono text-sm text-muted">0{i + 1}</span>
                </div>
                <h3 className="mt-5 text-lg font-semibold">{s.title}</h3>
                <p className="mt-2 leading-relaxed text-ink-soft">{s.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section id="features" className="container-page scroll-mt-16 py-20 sm:py-24">
        <p className="eyebrow">Under the hood</p>
        <h2 className="mt-3 max-w-2xl text-3xl font-semibold tracking-tight sm:text-4xl">
          A full editing team, compressed into one pipeline.
        </h2>
        <div className="mt-10 grid gap-px overflow-hidden rounded-card border border-line bg-line sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((f) => (
            <div key={f.title} className="bg-surface p-6">
              <span className="grid size-10 place-items-center rounded-lg bg-gold-soft">
                <f.icon className="size-5 text-gold-ink" aria-hidden />
              </span>
              <h3 className="mt-4 font-semibold">{f.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-ink-soft">{f.body}</p>
            </div>
          ))}
          <div className="flex flex-col justify-between gap-6 bg-ink p-6 text-paper">
            <p className="text-lg font-semibold leading-snug">Ready when you are.</p>
            <a href="#start" className="btn-primary self-start">
              Make Shorts
            </a>
          </div>
        </div>
      </section>
    </main>
  );
}
