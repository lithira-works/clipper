import { Flame } from "lucide-react";

/** Static 9:16 mock of a finished Short: hook banner, karaoke caption, score chip. */
export function PhonePreview() {
  return (
    <div className="relative mx-auto w-[260px] sm:w-[290px]" aria-hidden>
      <div className="absolute -inset-6 -z-10 rounded-[3rem] bg-gold-soft blur-2xl" />
      <div className="aspect-9/16 overflow-hidden rounded-[2.25rem] border-[6px] border-ink bg-ink shadow-(--shadow-card)">
        <div className="relative h-full w-full bg-[radial-gradient(120%_80%_at_50%_20%,#3a3833_0%,#0b0b0a_70%)]">
          {/* speaker silhouette */}
          <div className="absolute left-1/2 top-[28%] size-28 -translate-x-1/2 rounded-full bg-[#55524a]" />
          <div className="absolute left-1/2 top-[48%] h-52 w-48 -translate-x-1/2 rounded-t-[5rem] bg-[#45423b]" />

          <div className="absolute inset-x-5 top-8 rounded-md bg-gold px-3 py-2 text-center text-[13px] font-extrabold uppercase leading-tight text-ink">
            Nobody talks about this
          </div>

          <p className="absolute inset-x-4 bottom-[22%] text-center text-[26px] font-black uppercase leading-none tracking-tight text-white [text-shadow:0_3px_0_#000,0_0_8px_#000]">
            this <span className="mx-2 inline-block scale-110 text-gold">changed</span> everything
          </p>

          <div className="absolute bottom-4 left-4 flex items-center gap-1.5 rounded-full bg-white/95 px-2.5 py-1 text-xs font-bold text-ink">
            <Flame className="size-3.5 text-gold-strong" /> 94 viral score
          </div>
        </div>
      </div>
    </div>
  );
}
