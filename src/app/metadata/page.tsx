"use client";
import { FormEvent, Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  ArrowRight,
  Check,
  Database,
  FileText,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Trash2,
} from "lucide-react";
import { WorkspaceShell } from "@/components/workspace-shell";
import { api, Finding, MetadataRecord, Source } from "@/lib/api";

function MetadataInner() {
  const params = useSearchParams();
  const initialSource = params.get("source") || "";
  const initialCol = params.get("col") || "";
  const initialTbl = params.get("tbl") || "";

  const [sources, setSources] = useState<Source[]>([]);
  const [records, setRecords] = useState<MetadataRecord[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [form, setForm] = useState({
    source_id: initialSource,
    table_name: initialTbl,
    column_name: initialCol,
    purpose: "",
    retention: "",
  });

  function loadAll() {
    setLoading(true);
    Promise.all([
      api<Source[]>("/sources"),
      api<MetadataRecord[]>("/metadata"),
      api<Finding[]>("/findings"),
    ])
      .then(([srcs, metas, finds]) => {
        setSources(srcs);
        setRecords(metas);
        setFindings(finds);
        if (!form.source_id && srcs.length > 0) {
          setForm((f) => ({ ...f, source_id: String(srcs[0].id) }));
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    queueMicrotask(() => { void loadAll(); });
  }, []);

  async function handleSaveDeclaration(e: FormEvent) {
    e.preventDefault();
    if (!form.source_id || !form.column_name.trim()) {
      setError("Please select a data source and specify a column name.");
      return;
    }

    setBusy(true);
    setError("");
    setSuccess("");

    try {
      await api("/metadata", {
        method: "POST",
        body: JSON.stringify({
          source_id: Number(form.source_id),
          table_name: form.table_name.trim(),
          column_name: form.column_name.trim(),
          purpose: form.purpose.trim(),
          retention: form.retention.trim(),
        }),
      });
      setSuccess(`Declared metadata saved for "${form.column_name}".`);
      setForm((f) => ({ ...f, column_name: "", purpose: "", retention: "" }));
      loadAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save declaration.");
    } finally {
      setBusy(false);
    }
  }

  const unmappedFindings = findings.filter((f) => !f.purpose || !f.retention);

  return (
    <>
      <div className="content-heading">
        <div>
          <span className="eyebrow">GOVERNANCE &amp; RETENTION MANAGEMENT</span>
          <h2>Purpose &amp; Retention Declaration Center</h2>
          <p>
            Declare organizational business purposes and formal retention schedules for discovered fields. Privexis tracks missing documentation as technical evidence gaps without inferring automatic legal violations.
          </p>
        </div>
        <Link href="/evidence-gaps" className="button button-small button-outline">
          View Gap Analysis &rarr;
        </Link>
      </div>

      {error && (
        <div className="notice notice-error" role="alert">
          {error}
          <button className="notice-close" onClick={() => setError("")}>×</button>
        </div>
      )}
      {success && (
        <div className="notice notice-success" role="status">
          <Check size={16} />
          {success}
          <button className="notice-close" onClick={() => setSuccess("")}>×</button>
        </div>
      )}

      {/* Field Mapping Form & Current Records */}
      <div className="split-panels metadata-split">
        {/* Declaration Form */}
        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">NEW DECLARATION</span>
              <h3>Map Field Metadata</h3>
            </div>
          </div>

          <form onSubmit={handleSaveDeclaration} className="form-stack mapping-form">
            <label>
              Data Source
              <select
                required
                value={form.source_id}
                onChange={(e) => setForm({ ...form, source_id: e.target.value })}
                disabled={busy}
              >
                <option value="">Select a registered source</option>
                {sources.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.kind.toUpperCase()})
                  </option>
                ))}
              </select>
            </label>

            <label>
              Table / Database Scope
              <input
                value={form.table_name}
                onChange={(e) => setForm({ ...form, table_name: e.target.value })}
                placeholder="Optional (e.g. users, members, or blank for CSV)"
                disabled={busy}
              />
            </label>

            <label>
              Target Column Name
              <input
                required
                value={form.column_name}
                onChange={(e) => setForm({ ...form, column_name: e.target.value })}
                placeholder="e.g. contact_email, date_of_birth"
                disabled={busy}
              />
            </label>

            <label>
              Declared Business Purpose
              <textarea
                value={form.purpose}
                onChange={(e) => setForm({ ...form, purpose: e.target.value })}
                placeholder="State the organization-approved business purpose (e.g. Account Registration, Billing, Order Fulfillment)"
                disabled={busy}
              />
            </label>

            <label>
              Declared Retention Period / Schedule
              <input
                value={form.retention}
                onChange={(e) => setForm({ ...form, retention: e.target.value })}
                placeholder="Approved schedule (e.g. 7 years statutory, 30 days post-account deletion)"
                disabled={busy}
              />
            </label>

            <button className="button" disabled={busy}>
              {busy ? "Saving Declaration…" : "Save Declared Metadata"}
            </button>
          </form>

          <p className="privacy-hint">
            Organizational declarations represent technical documentation provided by data stewards. They do not constitute automatic legal justification.
          </p>
        </section>

        {/* Currently Declared Records */}
        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">DOCUMENTED METADATA</span>
              <h3>Mapped Declarations <span className="count-badge">{records.length}</span></h3>
            </div>
            <button className="icon-button" onClick={loadAll} title="Refresh records" aria-label="Refresh records">
              <RefreshCw size={15} />
            </button>
          </div>

          {records.length > 0 ? (
            <div className="metadata-list" style={{ maxHeight: 520, overflowY: "auto" }}>
              {records.map((r) => (
                <div className="metadata-row" key={r.id}>
                  <b>{r.column_name}</b>
                  <small>
                    Source: {r.source} {r.table_name ? `(${r.table_name})` : ""}
                  </small>
                  <div>
                    <span>
                      Purpose: <strong>{r.purpose || "Not declared"}</strong>
                    </span>
                    <span>
                      Retention: <strong>{r.retention || "Not declared"}</strong>
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <span className="empty-icon"><FileText size={21} /></span>
              <h3>No metadata declarations yet</h3>
              <p>Map purpose and retention rules to eliminate evidence gaps across discovered candidate fields.</p>
            </div>
          )}
        </section>
      </div>

      {/* Unmapped Candidate Findings Needing Context */}
      <section className="panel" style={{ marginTop: 20 }}>
        <div className="panel-heading">
          <div>
            <span className="eyebrow">ATTENTION NEEDED</span>
            <h3>Candidate Fields Missing Governance Context <span className="count-badge">{unmappedFindings.length}</span></h3>
          </div>
          <Link href="/evidence-gaps">View Gap Analysis &rarr;</Link>
        </div>

        {unmappedFindings.length > 0 ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Field</th>
                  <th>Source</th>
                  <th>Class</th>
                  <th>Confidence</th>
                  <th>Purpose</th>
                  <th>Retention</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {unmappedFindings.map((f) => (
                  <tr key={f.id}>
                    <td><strong>{f.column_name}</strong></td>
                    <td>{f.source}</td>
                    <td><span className="class-chip">{f.data_class}</span></td>
                    <td>{f.confidence}</td>
                    <td>
                      {f.purpose ? (
                        f.purpose
                      ) : (
                        <span className="missing-tag">Missing Purpose</span>
                      )}
                    </td>
                    <td>
                      {f.retention ? (
                        f.retention
                      ) : (
                        <span className="missing-tag">Missing Retention</span>
                      )}
                    </td>
                    <td>
                      <button
                        className="button button-small button-outline"
                        style={{ fontSize: 9, padding: "0 8px" }}
                        onClick={() => {
                          setForm({
                            source_id: String(f.source_id),
                            table_name: f.table_name,
                            column_name: f.column_name,
                            purpose: f.purpose || "",
                            retention: f.retention || "",
                          });
                          window.scrollTo({ top: 120, behavior: "smooth" });
                        }}
                      >
                        Fill Form
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="panel-note">
            All discovered personal data candidates currently have declared purpose and retention schedules.
          </p>
        )}
      </section>

      <div className="disclaimer-line">
        <ShieldCheck size={15} />
        Declared metadata records provide traceable documentation for compliance audits. Privexis does not validate legal sufficiency.
      </div>
    </>
  );
}

export default function MetadataPage() {
  return (
    <WorkspaceShell title="Metadata Management">
      <Suspense fallback={<div>Loading metadata management…</div>}>
        <MetadataInner />
      </Suspense>
    </WorkspaceShell>
  );
}

