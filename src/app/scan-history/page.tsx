"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Check,
  CheckCircle2,
  ClipboardCheck,
  Database,
  History,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { WorkspaceShell } from "@/components/workspace-shell";
import { api, Scan } from "@/lib/api";

export default function ScanHistoryPage() {
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  function loadScans() {
    setLoading(true);
    api<Scan[]>("/scans")
      .then((data) => {
        setScans(data);
        setError("");
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    queueMicrotask(() => { void loadScans(); });
  }, []);

  return (
    <WorkspaceShell title="Scan Execution History">
      <div className="content-heading">
        <div>
          <span className="eyebrow">AUDITABLE SCAN TRACE</span>
          <h2>Discovery Execution History</h2>
          <p>
            Execution journal with sample limits, rule versions, enabled class checklist, and results for each scan.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="button button-outline button-small" onClick={loadScans} disabled={loading}>
            <RefreshCw size={14} className={loading ? "spin" : ""} /> Refresh
          </button>
          <Link href="/scanner" className="button button-small">
            Start New Scan &rarr;
          </Link>
        </div>
      </div>

      {error && (
        <div className="notice notice-error" role="alert">
          {error}
          <button className="notice-close" onClick={() => setError("")}>×</button>
        </div>
      )}

      {/* History Table */}
      <section className="panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">EXECUTIONS</span>
            <h3>Recorded Runs <span className="count-badge">{scans.length}</span></h3>
          </div>
        </div>

        {scans.length > 0 ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Scan ID</th>
                  <th>Source Repository</th>
                  <th>Execution Status</th>
                  <th>Columns Inspected</th>
                  <th>Sampled Rows</th>
                  <th>Candidate Findings</th>
                  <th>Rule Version</th>
                  <th>Enabled Class Rules</th>
                  <th>Run Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {scans.map((s) => (
                  <tr key={s.id}>
                    <td>
                      <code className="mono-cell" style={{ color: "#C4B4FA" }}>PX-SCAN-{String(s.id).padStart(4, "0")}</code>
                    </td>
                    <td>
                      <strong>{s.source_name}</strong>
                    </td>
                    <td>
                      <span className={`status-pill status-${s.status}`}>
                        {s.status.toUpperCase()}
                      </span>
                    </td>
                    <td>{s.inspected_columns}</td>
                    <td>{s.rows_sampled}</td>
                    <td>
                      <span style={{ color: "#F2F4FA", fontWeight: 700 }}>
                        {s.findings_count !== undefined ? s.findings_count : "—"}
                      </span>
                    </td>
                    <td>
                      <code className="mono-cell">{s.rule_version}</code>
                    </td>
                    <td>{(s.enabled_classes || ["C1", "C2", "C3", "C4", "C5"]).join(", ")}</td>
                    <td>
                      <small style={{ color: "#A1A8B8" }}>
                        {new Date(s.created_at).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" })}
                      </small>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <span className="empty-icon"><History size={21} /></span>
            <h3>No discovery scans executed yet</h3>
            <p>Initiate a scan on a registered data source to create your first execution record.</p>
            <Link href="/scanner" className="button button-small">
              Go to Discovery Scanner
            </Link>
          </div>
        )}
      </section>

      <div className="disclaimer-line">
        <ShieldCheck size={15} />
        All scan executions are permanently logged to the tamper-evident audit record.
      </div>
    </WorkspaceShell>
  );
}

