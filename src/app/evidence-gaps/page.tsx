"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowDownToLine,
  ArrowRight,
  Check,
  ClipboardCheck,
  FileText,
  Filter,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import { WorkspaceShell } from "@/components/workspace-shell";
import { api, download, EvidenceGapsData, GapItem } from "@/lib/api";

export default function EvidenceGapsPage() {
  const [data, setData] = useState<EvidenceGapsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState<"all" | "purpose" | "retention" | "review">("all");

  function loadGaps() {
    setLoading(true);
    api<EvidenceGapsData>("/evidence-gaps")
      .then((res) => {
        setData(res);
        setError("");
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    queueMicrotask(() => { void loadGaps(); });
  }, []);

  async function handleDownloadGapsCsv() {
    try {
      await download("/reports/gaps.csv", "privexis-evidence-gaps.csv");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed.");
    }
  }

  const missingPurpose = data?.missing_purpose || [];
  const missingRetention = data?.missing_retention || [];
  const pendingReview = data?.pending_review || [];

  // Combine unique items for "all"
  const allGapMap = new Map<number, GapItem>();
  [...missingPurpose, ...missingRetention, ...pendingReview].forEach((item) => {
    allGapMap.set(item.id, item);
  });
  const allGaps = Array.from(allGapMap.values());

  const displayedItems =
    activeTab === "purpose"
      ? missingPurpose
      : activeTab === "retention"
      ? missingRetention
      : activeTab === "review"
      ? pendingReview
      : allGaps;

  const score = data?.completeness_score ?? 100;
  const scoreColor = score >= 80 ? "#63B79B" : score >= 50 ? "#D7AD62" : "#D87980";

  return (
    <WorkspaceShell title="Evidence Gap Analysis">
      <div className="content-heading">
        <div>
          <span className="eyebrow">DEFENSIBILITY AUDIT</span>
          <h2>Privacy Governance Gap Analysis</h2>
          <p>
            Identify unmapped purpose declarations, missing retention schedules, and unreviewed personal data candidates. Privexis tracks documentation debt to help your team achieve evidence completeness.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="button button-outline button-small" onClick={loadGaps} disabled={loading}>
            <RefreshCw size={14} className={loading ? "spin" : ""} /> Refresh
          </button>
          <button className="button button-small" onClick={handleDownloadGapsCsv}>
            <ArrowDownToLine size={14} /> Export Gaps CSV
          </button>
        </div>
      </div>

      {error && (
        <div className="notice notice-error" role="alert">
          {error}
          <button className="notice-close" onClick={() => setError("")}>×</button>
        </div>
      )}

      {/* Completeness Score Card */}
      <section className="panel" style={{ padding: "20px 24px", marginBottom: 20 }}>
        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: 20 }}>
          <div style={{ flex: 1, minWidth: 260 }}>
            <span className="eyebrow" style={{ color: "#9B83E8" }}>METADATA COMPLETENESS INDEX</span>
            <div style={{ display: "flex", alignItems: "baseline", gap: 14, margin: "6px 0 10px" }}>
              <span style={{ fontSize: 42, fontWeight: 800, fontFamily: "var(--font-mono)", color: scoreColor, lineHeight: 1 }}>
                {loading ? "…" : `${score}%`}
              </span>
              <span style={{ color: "#A1A8B8", fontSize: 13 }}>
                {score >= 80 ? "High Defensibility Posture" : score >= 50 ? "Moderate Documentation Gaps" : "Substantial Documentation Debt"}
              </span>
            </div>
            <div style={{ height: 6, background: "#1F2330", borderRadius: 3, overflow: "hidden", maxWidth: 480 }}>
              <div style={{ height: "100%", width: `${score}%`, background: scoreColor, transition: "width 0.4s ease" }} />
            </div>
          </div>

          <div style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>
            <div style={{ padding: "10px 16px", background: "#151822", border: "1px solid #282D3B", borderRadius: 6, textAlign: "center" }}>
              <span style={{ fontSize: 9, color: "#818897", display: "block" }}>DISCOVERED CANDIDATES</span>
              <b style={{ fontSize: 20, fontFamily: "var(--font-mono)" }}>{data?.total_findings || 0}</b>
            </div>
            <div style={{ padding: "10px 16px", background: "#151822", border: "1px solid #282D3B", borderRadius: 6, textAlign: "center" }}>
              <span style={{ fontSize: 9, color: "#D87980", display: "block" }}>MISSING PURPOSE</span>
              <b style={{ fontSize: 20, fontFamily: "var(--font-mono)", color: "#D87980" }}>{data?.counts.missing_purpose || 0}</b>
            </div>
            <div style={{ padding: "10px 16px", background: "#151822", border: "1px solid #282D3B", borderRadius: 6, textAlign: "center" }}>
              <span style={{ fontSize: 9, color: "#D7AD62", display: "block" }}>MISSING RETENTION</span>
              <b style={{ fontSize: 20, fontFamily: "var(--font-mono)", color: "#D7AD62" }}>{data?.counts.missing_retention || 0}</b>
            </div>
            <div style={{ padding: "10px 16px", background: "#151822", border: "1px solid #282D3B", borderRadius: 6, textAlign: "center" }}>
              <span style={{ fontSize: 9, color: "#9B83E8", display: "block" }}>UNREVIEWED</span>
              <b style={{ fontSize: 20, fontFamily: "var(--font-mono)", color: "#9B83E8" }}>{data?.counts.pending_review || 0}</b>
            </div>
          </div>
        </div>
      </section>

      {/* Tab Filter */}
      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <button
          className={activeTab === "all" ? "button button-small" : "button button-small button-outline"}
          onClick={() => setActiveTab("all")}
        >
          All Gaps ({allGaps.length})
        </button>
        <button
          className={activeTab === "purpose" ? "button button-small" : "button button-small button-outline"}
          onClick={() => setActiveTab("purpose")}
        >
          Missing Purpose ({missingPurpose.length})
        </button>
        <button
          className={activeTab === "retention" ? "button button-small" : "button button-small button-outline"}
          onClick={() => setActiveTab("retention")}
        >
          Missing Retention ({missingRetention.length})
        </button>
        <button
          className={activeTab === "review" ? "button button-small" : "button button-small button-outline"}
          onClick={() => setActiveTab("review")}
        >
          Pending Review ({pendingReview.length})
        </button>
      </div>

      {/* Gaps Table */}
      <section className="panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">ACTIONABLE REMEDIATION</span>
            <h3>Specific Defensibility Gaps <span className="count-badge">{displayedItems.length}</span></h3>
          </div>
        </div>

        {displayedItems.length > 0 ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Field Identifier</th>
                  <th>Source / Table</th>
                  <th>Class</th>
                  <th>Review Status</th>
                  <th>Purpose Declaration</th>
                  <th>Retention Schedule</th>
                  <th>Remediation Action</th>
                </tr>
              </thead>
              <tbody>
                {displayedItems.map((item) => {
                  const hasPurpose = Boolean(item.purpose);
                  const hasRetention = Boolean(item.retention);
                  const isPending = item.review_status === "pending";

                  return (
                    <tr key={item.id}>
                      <td>
                        <strong>{item.column_name}</strong>
                      </td>
                      <td>
                        {item.source_name} {item.table_name ? `(${item.table_name})` : ""}
                      </td>
                      <td>
                        <span className="class-chip">{item.data_class}</span> {item.class_name}
                      </td>
                      <td>
                        <span className={`status-pill status-${item.review_status}`}>{item.review_status}</span>
                      </td>
                      <td>
                        {hasPurpose ? (
                          <span style={{ color: "#9FD0B8" }}>{item.purpose}</span>
                        ) : (
                          <span className="missing-tag">Missing Purpose</span>
                        )}
                      </td>
                      <td>
                        {hasRetention ? (
                          <span style={{ color: "#9FD0B8" }}>{item.retention}</span>
                        ) : (
                          <span className="missing-tag">Missing Schedule</span>
                        )}
                      </td>
                      <td>
                        <div style={{ display: "flex", gap: 6 }}>
                          {!hasPurpose || !hasRetention ? (
                            <Link
                              href={`/metadata?source=${item.source_id}&col=${encodeURIComponent(item.column_name)}`}
                              className="button button-small button-outline"
                              style={{ fontSize: 9, padding: "0 8px" }}
                            >
                              Declare Metadata
                            </Link>
                          ) : null}
                          {isPending ? (
                            <Link
                              href={`/review?id=${item.id}`}
                              className="button button-small"
                              style={{ fontSize: 9, padding: "0 8px" }}
                            >
                              Review Candidate
                            </Link>
                          ) : null}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <span className="empty-icon"><ShieldCheck size={21} /></span>
            <h3>No evidence gaps found in this category</h3>
            <p>All candidates in this scope have verified determinations and declared metadata.</p>
          </div>
        )}
      </section>

      <div className="disclaimer-line">
        <ShieldCheck size={15} />
        Missing metadata flags technical documentation gaps. It does not automatically represent a regulatory violation.
      </div>
    </WorkspaceShell>
  );
}

