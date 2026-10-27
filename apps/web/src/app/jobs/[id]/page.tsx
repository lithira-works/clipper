import type { Metadata } from "next";
import { JobView } from "@/components/job-view";

export const metadata: Metadata = { title: "Your Shorts" };

export default async function JobPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <JobView id={id} />;
}
