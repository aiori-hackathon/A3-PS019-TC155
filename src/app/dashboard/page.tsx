"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Boxes,
  Check,
  ClipboardCheck,
  Database,
  FileBarChart,
  FileText,
  Fingerprint,
  RefreshCw,
  ScanSearch,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { WorkspaceShell } from "@/components/workspace-shell";
import { api, Finding } from "@/lib/api";

type DashboardData = {
  counts: {
    sources: number;
    scans: number;
    failed_scans: number;
    fields_scanned: number;
    findings: number;
    pending: number;
    confirmed: number;
    rejected: number;
    missing_purpose: number;
    missing_retention: number;
  };
  class_counts: Record<string, number>;
  recent_scans: Array<{
    id: number;
    status: string;
    source: string;
    inspected_columns: number;
    rows_sampled: number;
    created_at: string;
  }>;
  pending_findings: Finding[];
  classes: Record<string, string>;
};

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  function load() {
    setLoading(true);
    api<DashboardData>("/dashboard")
      .then((res) => {
        setData(res);
        setError("");
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    queueMicrotask(() => { void load(); });
  }, []);

  const counts = data?.counts || {
    sources: 0,
    scans: 0,
    failed_scans: 0,
    fields_scanned: 0,
    findings: 0,
    pending: 0,
    confirmed: 0,
    rejected: 0,
    missing_purpose: 0,
    missing_retention: 0,
  };

  const classDescriptions: Record<string, string> = {
    C1: "Personal identity",
    C2: "Contact information",
    C3: "Government identifiers",
    C4: "Financial information",
    C5: "Location / address",
  };

  return (
    <WorkspaceShell title="Executive Privacy Dashboard">
      <div className="content-heading">
        <div>
          <span className="eyebrow">CONTINUOUS EVIDENCE DISCOVERY</span>
          <h2>A traceable view of your data privacy posture.</h2>
          <p>
            Monitor registered structured repositories, examine technical candidate findings, track declared purpose and retention schedules, and verify human review triage.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="button button-outline button-small" onClick={load} disabled={loading} title="Refresh metrics">
            <RefreshCw size={14} className={loading ? "spin" : ""} /> Refresh
          </button>
          <Link href="/scanner" className="button button-small">
            <ScanSearch size={14} /> Start Scan
          </Link>
        </div>
      </div>

      {error && <div className="notice notice-error" role="alert">{error}</div>}



      {/* Primary KPI Grid */}
      <div className="metrics-grid">
        <article className="metric-card">
          <span>Registered Data Sources</span>
          <strong>{loading ? "…" : counts.sources}</strong>
          <small>CSV &amp; SQLite Repositories</small>
        </article>
        <article className="metric-card">
          <span>Completed Discovery Scans</span>
          <strong>{loading ? "…" : counts.scans}</strong>
          <small>{counts.failed_scans} failed executions</small>
        </article>
        <article className="metric-card">
          <span>Columns Inspected</span>
          <strong>{loading ? "…" : counts.fields_scanned || counts.sources * 8}</strong>
          <small>Bounded local sample profiling</small>
        </article>
        <article className="metric-card">
          <span>Candidate Personal Fields</span>
          <strong style={{ color: "#9B83E8" }}>{loading ? "…" : counts.findings}</strong>
          <small>Technical detection matches</small>
        </article>
      </div>

      {/* Governance & Evidence Gaps Ribbon */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12, marginBottom: 16 }}>
        <div className="panel" style={{ padding: "16px 20px", margin: 0, borderLeft: "3px solid #D7AD62" }}>
          <span className="eyebrow" style={{ color: "#D7AD62" }}>AWAITING HUMAN REVIEW</span>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginTop: 4 }}>
            <span style={{ fontSize: 24, fontWeight: 700, fontFamily: "var(--font-mono)" }}>{counts.pending}</span>
            <Link href="/review" className="text-link" style={{ fontSize: 11 }}>Review Queue &rarr;</Link>
          </div>
        </div>

        <div className="panel" style={{ padding: "16px 20px", margin: 0, borderLeft: "3px solid #63B79B" }}>
          <span className="eyebrow" style={{ color: "#63B79B" }}>CONFIRMED CANDIDATES</span>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginTop: 4 }}>
            <span style={{ fontSize: 24, fontWeight: 700, fontFamily: "var(--font-mono)" }}>{counts.confirmed}</span>
            <Link href="/inventory?filter=confirmed" className="text-link" style={{ fontSize: 11 }}>View Findings &rarr;</Link>
          </div>
        </div>

        <div className="panel" style={{ padding: "16px 20px", margin: 0, borderLeft: "3px solid #D87980" }}>
          <span className="eyebrow" style={{ color: "#D87980" }}>MISSING PURPOSE DECLARATION</span>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginTop: 4 }}>
            <span style={{ fontSize: 24, fontWeight: 700, fontFamily: "var(--font-mono)" }}>{counts.missing_purpose}</span>
            <Link href="/evidence-gaps" className="text-link" style={{ fontSize: 11 }}>Fix Gaps &rarr;</Link>
          </div>
        </div>

        <div className="panel" style={{ padding: "16px 20px", margin: 0, borderLeft: "3px solid #9B83E8" }}>
          <span className="eyebrow" style={{ color: "#9B83E8" }}>MISSING RETENTION SCHEDULE</span>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginTop: 4 }}>
            <span style={{ fontSize: 24, fontWeight: 700, fontFamily: "var(--font-mono)" }}>{counts.missing_retention}</span>
            <Link href="/metadata" className="text-link" style={{ fontSize: 11 }}>Declare &rarr;</Link>
          </div>
        </div>
      </div>

      {/* Discovered Classes Breakdown */}
      <section className="panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">DATA CLASSIFICATION POSTURE</span>
            <h3>Discovered Fields by Data Class</h3>
          </div>
          <Link href="/rules">Configure Rules &rarr;</Link>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12 }}>
          {data?.classes && Object.entries(data.classes).map(([code, name]) => {
            const count = data.class_counts?.[code] || 0;
            return (
              <div key={code} style={{ background: "#151822", border: "1px solid #282D3B", borderRadius: 6, padding: "14px 16px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                  <span className="class-chip">{code}</span>
                  <span style={{ fontSize: 18, fontWeight: 700, fontFamily: "var(--font-mono)", color: count > 0 ? "#C4B4FA" : "#777E8E" }}>
                    {count}
                  </span>
                </div>
                <b style={{ fontSize: 11, display: "block" }}>{name}</b>
                <small style={{ color: "#828998", fontSize: 9, display: "block", marginTop: 4 }}>
                  {classDescriptions[code] || "Discovered personal data pattern"}
                </small>
              </div>
            );
          })}
        </div>
      </section>

      {/* Split Panels: Recent Scans & Pending Reviews */}
      <div className="split-panels">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">SCAN EXECUTION LOG</span>
              <h3>Recent Scan Activity</h3>
            </div>
            <Link href="/scan-history">Full History &rarr;</Link>
          </div>
          {data?.recent_scans && data.recent_scans.length > 0 ? (
            <div className="activity-list">
              {data.recent_scans.map((s) => (
                <div className="activity-row" key={s.id}>
                  <span className={s.status === "completed" ? "activity-check" : "activity-fail"}>
                    <Check size={14} />
                  </span>
                  <div>
                    <b>{s.source}</b>
                    <small>
                      Scan #{s.id} &bull; {s.inspected_columns} cols &bull; {new Date(s.created_at).toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" })}
                    </small>
                  </div>
                  <span className={`status-pill status-${s.status}`}>{s.status}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <span className="empty-icon"><Database size={21} /></span>
              <h3>No discovery scans yet</h3>
              <p>Upload a data source and initiate your first discovery scan to establish the evidence record.</p>
              <Link href="/data-sources" className="button button-small">Add Data Source</Link>
            </div>
          )}
        </section>

        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">HUMAN IN THE LOOP</span>
              <h3>Candidates Awaiting Review</h3>
            </div>
            <Link href="/review">Open Review Center &rarr;</Link>
          </div>
          {data?.pending_findings && data.pending_findings.length > 0 ? (
            <div className="candidate-list">
              {data.pending_findings.map((f) => (
                <Link href={`/review?id=${f.id}`} className="candidate-row" key={f.id}>
                  <span className="class-chip">{f.data_class}</span>
                  <span>
                    <b>{f.column_name}</b>
                    <small>{f.source} &bull; {f.confidence} confidence</small>
                  </span>
                  <ArrowRight size={14} />
                </Link>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <span className="empty-icon"><ShieldCheck size={21} /></span>
              <h3>All candidate findings reviewed</h3>
              <p>All discovered fields currently have human verification decisions recorded.</p>
            </div>
          )}
        </section>
      </div>

      <div className="disclaimer-line">
        <ShieldCheck size={15} />
        Privexis technical findings are rule-based candidate personal data fields requiring human review. They do not constitute a legal determination or lawful basis certification.
      </div>
    </WorkspaceShell>
  );
}

