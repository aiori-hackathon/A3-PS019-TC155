"use client";

import { Suspense, useMemo } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowRight, Search } from "lucide-react";
import { WorkspaceShell } from "@/components/workspace-shell";

const pages = [
  { title: "Start a scan", href: "/scanner", terms: "scan scanner discovery detect classify csv sqlite source", description: "Run the five-class scanner against a registered source." },
  { title: "Data sources and sample files", href: "/data-sources", terms: "upload source datasets files samples synthetic csv sqlite get started", description: "Upload a file or choose one of ten synthetic CSV and SQLite fixtures." },
  { title: "Findings inventory", href: "/inventory", terms: "findings inventory search candidate field class review", description: "Search, filter, export, and review detected candidate fields." },
  { title: "Purpose and retention metadata", href: "/metadata", terms: "purpose retention metadata missing declarations gap", description: "Record declared purpose and retention, and find fields with missing context." },
  { title: "Evaluation metrics", href: "/evaluation", terms: "evaluation precision recall f1 ground truth labels metrics accuracy", description: "Review synthetic per-class precision, recall, F1, and confusion counts." },
  { title: "Reports", href: "/reports", terms: "report export download json csv summary", description: "Download field inventory and technical summary reports." },
  { title: "Human review", href: "/review", terms: "review confirm reject uncertain decision evidence", description: "Record a human decision and review note for each candidate." },
  { title: "Evidence gaps", href: "/evidence-gaps", terms: "evidence gaps missing purpose retention", description: "See findings that still need review or metadata declarations." },
  { title: "Detection rules and five classes", href: "/rules", terms: "rules taxonomy personal identity contact government financial location aadhaar pan email phone address not personal data", description: "Explore the five classes and test field names against the configured rules." },
  { title: "Privexis assistant", href: "/assistant", terms: "assistant ai help guidance questions", description: "Get local guidance on scans, review, metadata, and evaluation." },
  { title: "Security", href: "/security", terms: "security privacy local read only retention safety", description: "Read about bounded scanning and data handling." },
];

function SearchResults() {
  const params = useSearchParams();
  const query = params.get("q")?.trim() || "";
  const matches = useMemo(() => {
    const words = query.toLowerCase().split(/\s+/).filter(Boolean);
    if (!words.length) return [];
    return pages.filter((page) => words.some((word) => `${page.title} ${page.terms} ${page.description}`.toLowerCase().includes(word)));
  }, [query]);

  return <WorkspaceShell title="Search Privexis">
    <div className="content-heading"><div><span className="eyebrow">SEARCH</span><h2>{query ? `Results for “${query}”` : "Search product features"}</h2><p>Find tools and guidance, or search your workspace findings directly.</p></div></div>
    {query ? <section className="panel"><div className="panel-heading"><div><span className="eyebrow">PRODUCT FEATURES</span><h3>{matches.length} matching page{matches.length === 1 ? "" : "s"}</h3></div></div>{matches.length ? <div className="finding-list">{matches.map((page) => <Link className="candidate-row" href={page.href} key={page.href}><span><b>{page.title}</b><small>{page.description}</small></span><ArrowRight size={15} /></Link>)}</div> : <p className="panel-note">No feature pages matched. Try a shorter term or search findings below.</p>}<div className="panel-heading"><div><span className="eyebrow">YOUR WORKSPACE</span><h3>Search findings</h3></div></div><Link className="button" href={`/inventory?q=${encodeURIComponent(query)}`}><Search size={15} /> Search inventory for “{query}” <ArrowRight size={14} /></Link></section> : <div className="panel"><p className="panel-note">Enter a term in the navigation search to find product features or workspace findings.</p></div>}
  </WorkspaceShell>;
}

export default function SearchPage() {
  return <Suspense fallback={<div className="panel">Loading search…</div>}><SearchResults /></Suspense>;
}
