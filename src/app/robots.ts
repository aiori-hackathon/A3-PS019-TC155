import type { MetadataRoute } from "next";
export default function robots(): MetadataRoute.Robots {
  const site = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
  return { rules: [{ userAgent: "*", allow: ["/", "/features", "/how-it-works", "/security", "/documentation", "/about", "/faq", "/privacy", "/terms", "/contact"], disallow: ["/workspace"] }], sitemap: `${site}/sitemap.xml` };
}
