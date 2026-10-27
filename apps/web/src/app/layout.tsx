import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import "./globals.css";

const sans = Geist({ subsets: ["latin"], variable: "--font-geist-sans" });
const mono = Geist_Mono({ subsets: ["latin"], variable: "--font-geist-mono" });

export const metadata: Metadata = {
  title: { default: "Clipper — Viral Shorts from any YouTube video", template: "%s · Clipper" },
  description:
    "Paste a YouTube link. Clipper finds the most replayed, most viral moments and turns them into captioned 9:16 Shorts.",
};

export const viewport: Viewport = { themeColor: "#faf8f2" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable}`}>
      {/* Column shell: header, flexible main, footer pinned to the bottom on short pages. */}
      <body className="flex min-h-dvh flex-col overflow-x-clip font-sans">
        <SiteHeader />
        <div className="flex flex-1 flex-col">{children}</div>
        <SiteFooter />
      </body>
    </html>
  );
}
