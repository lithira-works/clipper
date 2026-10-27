import { Scissors } from "lucide-react";

export function SiteFooter() {
  return (
    <footer className="border-t border-line bg-surface">
      <div className="container-page flex flex-col gap-3 py-8 text-sm text-muted sm:flex-row sm:items-center sm:justify-between">
        <p className="flex items-center gap-2 font-medium text-ink">
          <Scissors className="size-4" aria-hidden /> Clipper
        </p>
        <p className="max-w-xl sm:text-right">
          Only clip videos you own or have permission to reuse. Respect creators and YouTube&apos;s
          Terms of Service.
        </p>
      </div>
    </footer>
  );
}
