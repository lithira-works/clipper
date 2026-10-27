import Link from "next/link";
import { Scissors } from "lucide-react";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-30 border-b border-line/80 bg-paper/85 backdrop-blur-md">
      <div className="container-page flex h-16 items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 font-semibold tracking-tight">
          <span className="grid size-8 place-items-center rounded-lg border-2 border-ink bg-gold">
            <Scissors className="size-4" strokeWidth={2.5} aria-hidden />
          </span>
          <span className="text-lg">Clipper</span>
        </Link>
        <nav className="flex items-center gap-1 text-sm text-ink-soft sm:gap-2">
          <Link href="/#how" className="hidden rounded-lg px-3 py-2 hover:text-ink sm:inline">
            How it works
          </Link>
          <Link href="/#features" className="hidden rounded-lg px-3 py-2 hover:text-ink sm:inline">
            Features
          </Link>
          <Link href="/#start" className="btn-ghost ml-1 py-2">
            New Shorts
          </Link>
        </nav>
      </div>
    </header>
  );
}
