import type { MetadataRoute } from "next";
const routes = ["", "features", "how-it-works", "security", "documentation", "about", "faq", "privacy", "terms", "contact"];
export default function sitemap(): MetadataRoute.Sitemap {
  const site = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
  return routes.map((route) => ({ url: `${site}/${route}`.replace(/\/$/, route ? "" : "/"), changeFrequency: route === "" ? "weekly" : "monthly", priority: route === "" ? 1 : 0.6 }));
}
