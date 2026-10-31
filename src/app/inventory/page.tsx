"use client";
import { Suspense, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  ArrowDownToLine,
  ArrowRight,
  Check,
  ClipboardCheck,
  Database,
  Filter,
  RefreshCw,
  Search,
  ShieldCheck,
} from "lucide-react";
import { WorkspaceShell } from "@/components/workspace-shell";
import { api, download, Finding } from "@/lib/api";

function InventoryInner() {
  const searchParams = useSearchParams();
  const initialFilter = searchParams.get("filter") || "all";

  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [q, setQ] = useState(searchParams.get("q") || "");
  const [statusFilter, setStatusFilter] = useState(initialFilter);
  const [classFilter, setClassFilter] = useState("all");
  const [confidenceFilter, setConfidenceFilter] = useState("all");

  function loadFindings() {
    setLoading(true);
    api<Finding[]>("/findings")
      .then((data) => {
        setFindings(data);
        setError("");
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    queueMicrotask(() => { void loadFindings(); });
  }, []);

  useEffect(() => {
    queueMicrotask(() => setQ(searchParams.get("q") || ""));
  }, [searchParams]);

  const filtered = useMemo(() => {
    return findings.filter((f) => {
      const matchStatus = statusFilter === "all" || f.review_status === statusFilter;
      const matchClass = classFilter === "all" || f.data_class === classFilter;
      const matchConf = confidenceFilter === "all" || f.confidence === confidenceFilter;
      const query = q.toLowerCase().trim();
      const matchQuery =
        !query ||
        f.column_name.toLowerCase().includes(query) ||
        f.table_name.toLowerCase().includes(query) ||
        f.source.toLowerCase().includes(query) ||
        f.data_class.toLowerCase().includes(query) ||
        f.class_name.toLowerCase().includes(query) ||
        f.rule_id.toLowerCase().includes(query);

      return matchStatus && matchClass && matchConf && matchQuery;
    });
  }, [findings, statusFilter, classFilter, confidenceFilter, q]);

  async function handleExportCsv() {
    try {
      await download("/reports/inventory.csv", "privexis-inventory.csv");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to download CSV.");
    }
  }

  return (
    <>
      <div className="content-heading">
        <div>
          <span className="eyebrow">VERIFIED PERSONAL DATA REGISTER</span>
          <h2>Candidate Personal Data Inventory</h2>
          <p>
            Examine discovered technical evidence across all scanned sources. Filter candidate fields, verify detection explanations, and link organizational purpose declarations.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="button button-outline button-small" onClick={loadFindings} disabled={loading}>
            <RefreshCw size={14} className={loading ? "spin" : ""} /> Refresh
          </button>
          <button className="button button-small" onClick={handleExportCsv}>
            <ArrowDownToLine size={14} /> Export CSV
          </button>
        </div>
      </div>

      {error && (
        <div className="notice notice-error" role="alert">
          {error}
          <button className="notice-close" onClick={() => setError("")}>×</button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <section className="panel" style={{ padding: "14px 18px", marginBottom: 16 }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center", justifyContent: "space-between" }}>
          <label className="search-box" style={{ flex: 1, minWidth: 260 }}>
            <Search size={16} />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search field name, source, class, or rule ID…"
              aria-label="Search candidate fields"
            />
          </label>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <select
              aria-label="Filter by review status"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{ minWidth: 140, height: 39, border: "1px solid #303543", borderRadius: 5, background: "#12151E", color: "#C3C7D1", padding: "0 10px", fontSize: 11 }}
            >
              <option value="all">All Review States</option>
              <option value="pending">Awaiting Review</option>
              <option value="confirmed">Confirmed</option>
              <option value="rejected">Rejected</option>
              <option value="uncertain">Uncertain</option>
            </select>

            <select
              aria-label="Filter by data class"
              value={classFilter}
              onChange={(e) => setClassFilter(e.target.value)}
              style={{ minWidth: 140, height: 39, border: "1px solid #303543", borderRadius: 5, background: "#12151E", color: "#C3C7D1", padding: "0 10px", fontSize: 11 }}
            >
              <option value="all">All Classes</option>
              <option value="C1">C1: Personal identity</option>
              <option value="C2">C2: Contact information</option>
              <option value="C3">C3: Government identifiers</option>
              <option value="C4">C4: Financial information</option>
              <option value="C5">C5: Location / address</option>
            </select>

            <select
              aria-label="Filter by confidence"
              value={confidenceFilter}
              onChange={(e) => setConfidenceFilter(e.target.value)}
              style={{ minWidth: 130, height: 39, border: "1px solid #303543", borderRadius: 5, background: "#12151E", color: "#C3C7D1", padding: "0 10px", fontSize: 11 }}
            >
              <option value="all">All Confidence</option>
              <option value="high">High Confidence</option>
              <option value="medium">Medium Confidence</option>
              <option value="low">Low Confidence</option>
            </select>
          </div>
        </div>
      </section>

      {/* Findings Listing */}
      <section className="panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">DISCOVERY INVENTORY</span>
            <h3>
              Discovered Personal Data Fields <span className="count-badge">{filtered.length} of {findings.length}</span>
            </h3>
          </div>
        </div>

        {filtered.length > 0 ? (
          <div className="finding-list">
            {filtered.map((item) => (
              <article className="finding-card" key={item.id}>
                <div className="finding-top">
                  <span className="class-chip">{item.data_class}</span>
                  <span className={`status-pill status-${item.review_status}`}>
                    {item.review_status}
                  </span>
                </div>

                <div className="finding-title">
                  <h3>{item.column_name}</h3>
                  <span>{item.source}{item.table_name ? ` / ${item.table_name}` : ""}</span>
                </div>

                <div className="finding-details">
                  <div>
                    <small>DATA CLASS</small>
                    <b>{item.class_name}</b>
                  </div>
                  <div>
                    <small>CONFIDENCE</small>
                    <b style={{ color: item.confidence === "high" ? "#63B79B" : "#D7AD62" }}>
                      {item.confidence.toUpperCase()}
                    </b>
                  </div>
                  <div style={{ gridColumn: "1/-1" }}>
                    <small>DETECTION RULE APPLIED</small>
                    <b className="mono-cell" style={{ color: "#C4B4FA" }}>{item.rule_id}</b>
                  </div>
                </div>

                <div className="evidence-box">
                  <b>Technical Evidence</b>
                  <p>{item.evidence}</p>
                </div>

                <div className="metadata-inline">
                  <div>
                    <small style={{ color: "#818897", fontSize: 9 }}>PURPOSE DECLARATION</small>
                    <b>{item.purpose ? item.purpose : <span className="missing-tag">Missing Declaration</span>}</b>
                  </div>
                  <div>
                    <small style={{ color: "#818897", fontSize: 9 }}>RETENTION SCHEDULE</small>
                    <b>{item.retention ? item.retention : <span className="missing-tag">Missing Declaration</span>}</b>
                  </div>

                  <div style={{ gridColumn: "1/-1", display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8 }}>
                    <Link
                      href={`/metadata?source=${item.source_id}&col=${encodeURIComponent(item.column_name)}&tbl=${encodeURIComponent(item.table_name)}`}
                      className="text-button"
                    >
                      Declare Metadata &rarr;
                    </Link>
                    <Link
                      href={`/review?id=${item.id}`}
                      className="button button-small button-outline"
                      style={{ fontSize: 10, padding: "0 10px" }}
                    >
                      Review Finding
                    </Link>
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <span className="empty-icon"><ClipboardCheck size={21} /></span>
            <h3>No matching candidate findings</h3>
            <p>
              {findings.length === 0
                ? "No discovery scans have been performed yet. Upload a source and run a scan."
                : "No fields match your search or filter criteria. Clear filters to show all."}
            </p>
            {findings.length === 0 && (
              <Link href="/data-sources" className="button button-small">
                Go to Data Sources &rarr;
              </Link>
            )}
          </div>
        )}
      </section>

      <div className="disclaimer-line">
        <ShieldCheck size={15} />
        Personal data candidates reflect technical matching against configured rules. Raw data values are not stored in inventory findings.
      </div>
    </>
  );
}

export default function InventoryPage() {
  return (
    <WorkspaceShell title="Personal Data Inventory">
      <Suspense fallback={<div>Loading inventory register…</div>}>
        <InventoryInner />
      </Suspense>
    </WorkspaceShell>
  );
}

