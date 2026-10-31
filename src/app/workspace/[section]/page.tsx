import { redirect } from "next/navigation";

const sectionToPath: Record<string, string> = {
  overview: "/dashboard",
  sources: "/data-sources",
  findings: "/inventory",
  metadata: "/metadata",
  evaluation: "/evaluation",
  reports: "/reports",
  assistant: "/assistant",
  settings: "/settings",
};

export default async function Page({ params }: { params: Promise<{ section: string }> }) {
  const { section } = await params;
  const target = sectionToPath[section] || "/dashboard";
  redirect(target);
}

