"use client";
import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  ArrowRight,
  Check,
  CheckCircle2,
  Clock,
  Fingerprint,
  HelpCircle,
  History,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { WorkspaceShell } from "@/components/workspace-shell";
import { api, Finding } from "@/lib/api";

type ReviewHistoryItem = {
  decision: string;
  note: string;
  user_id: number;
  created_at: string;
};

function ReviewInner() {
  const searchParams = useSearchParams();
  const targetId = searchParams.get("id");

  const [findings, setFindings] = useState<Finding[]>([]);
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [history, setHistory] = useState<ReviewHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [decision, setDecision] = useState("confirmed");
  const [note, setNote] = useState("");
  const [reclassify, setReclassify] = useState("");
  const [filter, setFilter] = useState("pending");

  function loadFindings(keepSelectedId?: number) {
    setLoading(true);
    api<Finding[]>("/findings")
      .then((data) => {
        setFindings(data);
        const selId = keepSelectedId || (targetId ? Number(targetId) : null);
        const found = selId ? data.find((f) => f.id === selId) : data[0];
        if (found) {
          selectFinding(found);
        } else if (data.length > 0) {
          selectFinding(data[0]);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    queueMicrotask(() => { void loadFindings(); });
  }, [targetId]);

  function selectFinding(f: Finding) {
    setSelectedFinding(f);
    setDecision(f.review_status !== "pending" ? f.review_status : "confirmed");
    setNote(f.review_note || "");
    setReclassify(f.data_class);
    setError("");
    setSuccess("");

    // Fetch review history
    api<ReviewHistoryItem[]>(`/findings/${f.id}/history`)
      .then((hist) => setHistory(hist))
      .catch(() => setHistory([]));
  }

  async function handleSaveReview(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedFinding) return;

    if (decision !== "uncertain" && note.trim().length < 4) {
      setError("Please provide a concise verification note (at least 4 characters) for audit trail compliance.");
      return;
    }

    setBusy(true);
    setError("");
    setSuccess("");

    try {
      await api(`/findings/${selectedFinding.id}/review`, {
        method: "POST",
        body: JSON.stringify({
          decision,
          note: note.trim() || "Verified in context.",
          reclassify: reclassify !== selectedFinding.data_class ? reclassify : null,
        }),
      });
      setSuccess(`Review decision "${decision.toUpperCase()}" saved to immutable audit history.`);
      loadFindings(selectedFinding.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to record review.");
    } finally {
      setBusy(false);
    }
  }

  const filteredList = findings.filter((f) => filter === "all" || f.review_status === filter);

  return (
    <>
      <div className="content-heading">
        <div>
          <span className="eyebrow">HUMAN IN THE LOOP</span>
          <h2>Evidence Review &amp; Triage Center</h2>
          <p>
            Verify candidate personal data findings, reject false positives, adjust classifications, and record auditable reasoning notes.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="button button-outline button-small" onClick={() => loadFindings(selectedFinding?.id)}>
            <RefreshCw size={14} className={loading ? "spin" : ""} /> Refresh
          </button>
        </div>
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

      {/* Review Workflow Split: Queue on Left, Detail & Actions on Right */}
      <div className="split-panels" style={{ gridTemplateColumns: "minmax(300px, 0.9fr) 1.1fr", alignItems: "start" }}>
        {/* Triage Queue */}
        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">CANDIDATE QUEUE</span>
              <h3>Review Queue <span className="count-badge">{filteredList.length}</span></h3>
            </div>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              style={{ padding: "4px 8px", background: "#171B27", border: "1px solid #282D3B", borderRadius: 4, color: "#C4B4FA", fontSize: 10 }}
            >
              <option value="pending">Awaiting Review</option>
              <option value="confirmed">Confirmed</option>
              <option value="rejected">Rejected</option>
              <option value="uncertain">Uncertain</option>
              <option value="all">All Findings</option>
            </select>
          </div>

          {filteredList.length > 0 ? (
            <div className="candidate-list" style={{ maxHeight: 580, overflowY: "auto" }}>
              {filteredList.map((item) => {
                const isSelected = selectedFinding?.id === item.id;
                return (
                  <div
                    key={item.id}
                    onClick={() => selectFinding(item)}
                    className="candidate-row"
                    style={{
                      cursor: "pointer",
                      padding: "10px 12px",
                      background: isSelected ? "#211D2E" : "transparent",
                      borderLeft: isSelected ? "3px solid #9B83E8" : "3px solid transparent",
                    }}
                  >
                    <span className="class-chip">{item.data_class}</span>
                    <span style={{ minWidth: 0, flex: 1 }}>
                      <b style={{ color: isSelected ? "#F2F4FA" : "#D4D7E2" }}>{item.column_name}</b>
                      <small style={{ color: "#828998" }}>{item.source} &bull; {item.confidence} conf</small>
                    </span>
                    <span className={`status-pill status-${item.review_status}`}>
                      {item.review_status}
                    </span>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="empty-state">
              <span className="empty-icon"><ShieldCheck size={21} /></span>
              <h3>Queue is clear</h3>
              <p>No findings match the current review state filter ({filter}).</p>
            </div>
          )}
        </section>

        {/* Selected Finding Review Action Panel */}
        {selectedFinding ? (
          <section className="panel" style={{ border: "1px solid #3B3448" }}>
            <div className="panel-heading">
              <div>
                <span className="eyebrow">EVIDENCE INSPECTION</span>
                <h3 style={{ fontSize: 16 }}>{selectedFinding.column_name}</h3>
              </div>
              <span className={`status-pill status-${selectedFinding.review_status}`}>
                {selectedFinding.review_status.toUpperCase()}
              </span>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, background: "#151822", padding: 14, borderRadius: 6, marginBottom: 14 }}>
              <div>
                <small style={{ color: "#818897", fontSize: 9 }}>SOURCE REPOSITORY</small>
                <b style={{ fontSize: 11, display: "block" }}>{selectedFinding.source}</b>
              </div>
              <div>
                <small style={{ color: "#818897", fontSize: 9 }}>TABLE / SCOPE</small>
                <b style={{ fontSize: 11, display: "block" }}>{selectedFinding.table_name || "Primary CSV"}</b>
              </div>
              <div>
                <small style={{ color: "#818897", fontSize: 9 }}>CURRENT DATA CLASS</small>
                <b style={{ fontSize: 11, display: "block", color: "#C4B4FA" }}>
                  {selectedFinding.data_class} &bull; {selectedFinding.class_name}
                </b>
              </div>
              <div>
                <small style={{ color: "#818897", fontSize: 9 }}>DETECTION CONFIDENCE</small>
                <b style={{ fontSize: 11, display: "block", color: selectedFinding.confidence === "high" ? "#63B79B" : "#D7AD62" }}>
                  {selectedFinding.confidence.toUpperCase()}
                </b>
              </div>
            </div>

            <div className="evidence-box" style={{ marginBottom: 16 }}>
              <b>Technical Evidence &amp; Detection Rule</b>
              <p>{selectedFinding.evidence}</p>
              <div style={{ marginTop: 6, fontSize: 10, color: "#C4B4FA", fontFamily: "var(--font-mono)" }}>
                Rule: {selectedFinding.rule_id}
              </div>
            </div>

            {/* Review Decision Form */}
            <form onSubmit={handleSaveReview} className="form-stack">
              <label>
                Human Review Decision
                <select value={decision} onChange={(e) => setDecision(e.target.value)} disabled={busy}>
                  <option value="confirmed">Confirm Candidate (Verified Personal Data)</option>
                  <option value="rejected">Reject Candidate (False Positive Match)</option>
                  <option value="uncertain">Mark Uncertain (Requires Further Investigation)</option>
                </select>
              </label>

              <label>
                Data Class Reclassification (Optional)
                <select value={reclassify} onChange={(e) => setReclassify(e.target.value)} disabled={busy}>
                  <option value="C1">C1: Personal identity</option>
                  <option value="C2">C2: Contact information</option>
                  <option value="C3">C3: Government identifiers</option>
                  <option value="C4">C4: Financial information</option>
                  <option value="C5">C5: Location / address</option>
                </select>
                <small>Select a different class if the rule engine misclassified the semantic type.</small>
              </label>

              <label>
                Audit Rationale &amp; Reviewer Notes
                <textarea
                  required={decision !== "uncertain"}
                  minLength={4}
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Record your justification for this determination (e.g. Verified customer registry schema, confirmed false positive code number)"
                  disabled={busy}
                  style={{ minHeight: 70 }}
                />
              </label>

              <div style={{ display: "flex", gap: 10, marginTop: 4 }}>
                <button className="button" type="submit" disabled={busy}>
                  {busy ? "Saving Decision…" : "Save Audit Decision"}
                </button>
                <Link
                  href={`/metadata?source=${selectedFinding.source_id}&col=${encodeURIComponent(selectedFinding.column_name)}`}
                  className="button button-outline"
                >
                  Declare Purpose/Retention &rarr;
                </Link>
              </div>
            </form>

            {/* Audit History of Decisions on This Finding */}
            <div style={{ marginTop: 24, borderTop: "1px solid #282D3B", paddingTop: 16 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                <History size={15} style={{ color: "#9B83E8" }} />
                <span className="eyebrow" style={{ color: "#A1A8B8" }}>AUDIT HISTORY FOR THIS FIELD</span>
              </div>

              {history.length > 0 ? (
                <div style={{ display: "grid", gap: 8 }}>
                  {history.map((h, i) => (
                    <div key={i} style={{ padding: 10, background: "#10121B", border: "1px solid #222632", borderRadius: 4, fontSize: 11 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                        <span className={`status-pill status-${h.decision}`}>{h.decision}</span>
                        <small style={{ color: "#777E8E" }}>
                          {new Date(h.created_at).toLocaleString(undefined, { dateStyle: "short", timeStyle: "short" })}
                        </small>
                      </div>
                      <p style={{ margin: 0, color: "#C5C8D4" }}>{h.note || "No note recorded."}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ fontSize: 10, color: "#818897", margin: 0 }}>
                  No prior review determinations logged for this candidate.
                </p>
              )}
            </div>
          </section>
        ) : (
          <div className="empty-state">
            <span className="empty-icon"><ShieldCheck size={21} /></span>
            <h3>No finding selected</h3>
            <p>Select a candidate from the queue on the left to inspect evidence and submit a determination.</p>
          </div>
        )}
      </div>

      <div className="disclaimer-line">
        <ShieldCheck size={15} />
        All reviewer decisions and rationales are logged to the immutable audit events log.
      </div>
    </>
  );
}

export default function ReviewPage() {
  return (
    <WorkspaceShell title="Evidence Review Center">
      <Suspense fallback={<div>Loading review center…</div>}>
        <ReviewInner />
      </Suspense>
    </WorkspaceShell>
  );
}

