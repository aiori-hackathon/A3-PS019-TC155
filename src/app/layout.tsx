import type { Metadata, Viewport } from "next";
import { FloatingAssistant } from "@/components/floating-assistant";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
  title: { default: "Privexis — Privacy evidence, made inspectable", template: "%s | Privexis" },
  description: "Discover candidate personal data, connect declared purpose and retention, and review technical evidence in one privacy engineering workspace.",
  openGraph: { title: "Privexis — Privacy evidence, made inspectable", description: "A technical evidence workbench for privacy engineering teams.", images: [{ url: "/brand/privexis-original.jpg", width: 1200, height: 628, alt: "Privexis — Detect. Decrypt. Defend." }] },
  icons: { icon: "/brand/privexis-favicon.png", apple: "/brand/privexis-apple-touch-icon.png" },
  applicationName: "Privexis",
  keywords: ["privacy engineering", "data discovery", "privacy evidence", "personal data inventory"],
  twitter: { card: "summary_large_image", title: "Privexis — Privacy evidence, made inspectable", description: "A technical evidence workbench for privacy engineering teams.", images: ["/brand/privexis-original.jpg"] },
  robots: { index: true, follow: true },
};
export const viewport: Viewport = { themeColor: "#090B12", colorScheme: "dark" };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}<FloatingAssistant /></body></html>; }
