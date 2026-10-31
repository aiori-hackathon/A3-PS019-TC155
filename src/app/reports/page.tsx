"use client";
import { useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowDownToLine,
  ExternalLink,
  FileBarChart,
  FileSpreadsheet,
  FileText,
  History,
  Printer,
  ShieldCheck,
} from "lucide-react";
import { WorkspaceShell } from "@/components/workspace-shell";
import { download } from "@/lib/api";

export default function ReportsPage() {
  const [downloading, setDownloading] = useState<string | null>(null);
  const [error, setError] = useState("");

  async function handleDownload(path: string, filename: string, key: string) {
    setDownloading(key);
    setError("");
    try {
      await download(path, filename);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed.");
    } finally {
      setDownloading(null);
    }
  }

  function handleOpenHtmlReport() {
    const apiOrigin = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    window.open(`${apiOrigin}/api/v1/reports/summary.html`, "_blank");
  }

  return (
    <WorkspaceShell title="Reports &amp; Evidence Packages">
      <div className="content-heading">
        <div>
          <span className="eyebrow">AUDITABLE EXPORT ARTIFACTS</span>
          <h2>Privacy Evidence &amp; Compliance Reporting</h2>
          <p>
            Generate and export structured evidence files, missing governance reports, review decision logs, and printable technical audit summaries.
          </p>
        </div>
      </div>

      {error && (
        <div className="notice notice-error" role="alert">
          {error}
          <button className="notice-close" onClick={() => setError("")}>×</button>
        </div>
      )}

      {/* Featured Printable Technical Audit Report */}
      <section
        className="panel"
        style={{
          background: "radial-gradient(ellipse at 90% 10%, #2A2145 0%, #11141D 60%)",
          border: "1px solid #4A3C6A",
          padding: 24,
          marginBottom: 20,
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16 }}>
          <div style={{ maxWidth: 600 }}>
            <span className="eyebrow" style={{ color: "#C4B4FA" }}>EXECUTIVE AUDIT SUMMARY</span>
            <h3 style={{ fontSize: 20, margin: "6px 0 10px" }}>Printable Technical Privacy Audit Report</h3>
            <p style={{ color: "#A1A8B8", fontSize: 11, lineHeight: 1.8, margin: 0 }}>
              Self-contained, beautifully styled technical audit report compiling total sources, discovery findings, declared metadata, and human verification status. Includes an inline browser print trigger to save as PDF.
            </p>
          </div>
          <button className="button" onClick={handleOpenHtmlReport} style={{ height: 42 }}>
            <Printer size={15} /> View &amp; Print Audit Report <ExternalLink size={13} />
          </button>
        </div>
      </section>

      {/* Downloadable Reports Grid */}
      <div className="report-grid">
        {/* Report 1: Inventory CSV */}
        <article className="report-card">
          <span className="report-glyph"><FileSpreadsheet size={19} /></span>
          <span className="eyebrow">CSV FORMAT / COMPREHENSIVE</span>
          <h3>Candidate Findings Inventory</h3>
          <p>
            Full tabular export of all discovered fields, source repositories, data classes, detection rules, confidence ratings, and review determinations.
          </p>
          <button
            className="button button-outline"
            disabled={downloading === "inventory_csv"}
            onClick={() => handleDownload("/reports/inventory.csv", "privexis-inventory.csv", "inventory_csv")}
          >
            <ArrowDownToLine size={15} /> {downloading === "inventory_csv" ? "Preparing…" : "Download Inventory (CSV)"}
          </button>
        </article>

        {/* Report 2: Missing Metadata Gaps CSV */}
        <article className="report-card">
          <span className="report-glyph"><AlertTriangle size={19} style={{ color: "#D7AD62" }} /></span>
          <span className="eyebrow">CSV FORMAT / GOVERNANCE DEBT</span>
          <h3>Evidence Gaps &amp; Missing Metadata</h3>
          <p>
            Export of all candidate personal data fields lacking declared business purpose or retention schedules for compliance remediation tracking.
          </p>
          <button
            className="button button-outline"
            disabled={downloading === "gaps_csv"}
            onClick={() => handleDownload("/reports/gaps.csv", "privexis-evidence-gaps.csv", "gaps_csv")}
          >
            <ArrowDownToLine size={15} /> {downloading === "gaps_csv" ? "Preparing…" : "Download Gaps Report (CSV)"}
          </button>
        </article>

        {/* Report 3: Review History Audit CSV */}
        <article className="report-card">
          <span className="report-glyph"><History size={19} style={{ color: "#63B79B" }} /></span>
          <span className="eyebrow">CSV FORMAT / AUDIT TRAIL</span>
          <h3>Human Review Activity Log</h3>
          <p>
            Auditable log of all human verification decisions, confirmation notes, false-positive rejections, reviewer identities, and timestamps.
          </p>
          <button
            className="button button-outline"
            disabled={downloading === "reviews_csv"}
            onClick={() => handleDownload("/reports/reviews.csv", "privexis-review-history.csv", "reviews_csv")}
          >
            <ArrowDownToLine size={15} /> {downloading === "reviews_csv" ? "Preparing…" : "Download Review Audit Log (CSV)"}
          </button>
        </article>

        {/* Report 4: Technical Summary JSON */}
        <article className="report-card">
          <span className="report-glyph"><ShieldCheck size={19} /></span>
          <span className="eyebrow">JSON FORMAT / MACHINE-READABLE</span>
          <h3>Technical Evidence Package</h3>
          <p>
            Cryptographic summary package with generation timestamps, organization metadata, synthetic evaluation metrics, and statutory limitations.
          </p>
          <button
            className="button button-outline"
            disabled={downloading === "summary_json"}
            onClick={() => handleDownload("/reports/summary.json", "privexis-summary.json", "summary_json")}
          >
            <ArrowDownToLine size={15} /> {downloading === "summary_json" ? "Preparing…" : "Download Summary Package (JSON)"}
          </button>
        </article>
      </div>

      <div className="disclaimer-line" style={{ marginTop: 24 }}>
        <ShieldCheck size={15} />
        All exported reports represent technical candidate evidence and declared governance metadata. They do not constitute legal advice or certify regulatory compliance.
      </div>
    </WorkspaceShell>
  );
}

