"use client";
import { FormEvent, Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  ArrowRight,
  Check,
  ClipboardCheck,
  Database,
  FileSpreadsheet,
  FileText,
  Play,
  RefreshCw,
  ScanSearch,
  ShieldCheck,
  Sliders,
} from "lucide-react";
import { WorkspaceShell } from "@/components/workspace-shell";
import { api, Source } from "@/lib/api";

type ScanResult = {
  id: number;
  status: string;
  inspected_columns: number;
  rows_sampled: number;
  findings: number;
  error?: string | null;
};

function ScannerInner() {
  const params = useSearchParams();
  const initialSource = params.get("source") || "";

  const [sources, setSources] = useState<Source[]>([]);
  const [selectedSourceId, setSelectedSourceId] = useState(initialSource);
  const [sampleLimit, setSampleLimit] = useState("500");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<ScanResult | null>(null);

  useEffect(() => {
    api<Source[]>("/sources")
      .then((data) => {
        setSources(data);
        if (!selectedSourceId && data.length > 0) {
          setSelectedSourceId(String(data[0].id));
        }
      })
      .catch((err) => setError(err.message));
  }, [selectedSourceId]);

  async function handleStartScan(e: FormEvent) {
    e.preventDefault();
    if (!selectedSourceId) {
      setError("Please select a registered data source.");
      return;
    }

    setBusy(true);
    setError("");
    setResult(null);

    try {
      const res = await api<ScanResult>(`/sources/${selectedSourceId}/scan?sample_limit=${encodeURIComponent(sampleLimit)}`, {
        method: "POST",
      });
      if (res.status === "failed") {
        setError(res.error || "Discovery scan failed. Please check source integrity.");
      } else {
        setResult(res);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run scan.");
    } finally {
      setBusy(false);
    }
  }

  const selectedSource = sources.find((s) => String(s.id) === selectedSourceId);

  return (
    <>
      <div className="content-heading">
        <div>
          <span className="eyebrow">DISCOVERY EXECUTION ENGINE</span>
          <h2>Automated Personal Data Scanner</h2>
          <p>
            Choose a bounded row sample and scan registered CSV or SQLite sources against all five configured personal-data classes.
          </p>
        </div>
        <Link href="/scan-history" className="button button-small button-outline">
          View Scan History &rarr;
        </Link>
      </div>

      {error && (
        <div className="notice notice-error" role="alert">
          {error}
          <button className="notice-close" onClick={() => setError("")}>×</button>
        </div>
      )}

      {/* Scan Configuration Form */}
      <div className="split-panels" style={{ alignItems: "start" }}>
        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">CONFIGURATION WIZARD</span>
              <h3>Scan Parameters</h3>
            </div>
          </div>

          <form onSubmit={handleStartScan} className="form-stack">
            <label>
              Select Target Data Source
              {sources.length > 0 ? (
                <select
                  value={selectedSourceId}
                  onChange={(e) => setSelectedSourceId(e.target.value)}
                  disabled={busy}
                  required
                >
                  {sources.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.kind.toUpperCase()} &bull; {(s.size_bytes / 1024).toFixed(1)} KB)
                    </option>
                  ))}
                </select>
              ) : (
                <div style={{ padding: 12, background: "#171B27", border: "1px solid #282D3B", borderRadius: 4, color: "#A1A8B8", fontSize: 11 }}>
                  No sources available. <Link href="/data-sources" style={{ color: "#9B83E8" }}>Add a source first</Link>.
                </div>
              )}
            </label>

            <label>
              Row Sampling Limit
              <select value={sampleLimit} onChange={(e) => setSampleLimit(e.target.value)} disabled={busy}>
                <option value="100">100 rows (Ultra-fast profile)</option>
                <option value="500">500 rows (Balanced default)</option>
                <option value="1000">1,000 rows (Comprehensive inspection)</option>
                <option value="5000">5,000 rows (Maximum depth sample)</option>
              </select>
              <small>Profiles bounded rows in memory; raw sample records are never saved to the database.</small>
            </label>

            <button
              className="button"
              type="submit"
              disabled={busy || sources.length === 0}
              style={{ marginTop: 8 }}
            >
              {busy ? (
                <>
                  <RefreshCw size={15} className="spin" /> Scanning in Progress…
                </>
              ) : (
                <>
                  <Play size={15} /> Execute Discovery Scan
                </>
              )}
            </button>
          </form>
        </section>

        {/* Target Details & Status Card */}
        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">INSPECTION PROFILE</span>
              <h3>Source Blueprint</h3>
            </div>
          </div>

          {selectedSource ? (
            <div style={{ display: "grid", gap: 14 }}>
              <div style={{ padding: 16, background: "#151822", border: "1px solid #282D3B", borderRadius: 6 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                  {selectedSource.kind === "sqlite" ? (
                    <Database size={18} style={{ color: "#9B83E8" }} />
                  ) : (
                    <FileSpreadsheet size={18} style={{ color: "#9B83E8" }} />
                  )}
                  <b style={{ fontSize: 13 }}>{selectedSource.name}</b>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, fontSize: 11, color: "#818897" }}>
                  <span>Type: <strong style={{ color: "#F2F4FA" }}>{selectedSource.kind.toUpperCase()}</strong></span>
                  <span>Size: <strong style={{ color: "#F2F4FA" }}>{(selectedSource.size_bytes / 1024).toFixed(1)} KB</strong></span>
                  <span>Registered: <strong style={{ color: "#F2F4FA" }}>{new Date(selectedSource.created_at).toLocaleDateString()}</strong></span>
                  <span>Engine: <strong style={{ color: "#63B79B" }}>Read-Only</strong></span>
                </div>
              </div>

              <div style={{ padding: 14, background: "#12141E", border: "1px solid #242836", borderRadius: 6, fontSize: 11, color: "#A1A8B8", lineHeight: 1.6 }}>
                <b style={{ color: "#F2F4FA", display: "block", marginBottom: 4 }}>Inspection Rules Applied:</b>
                &bull; C1 Personal identity: name, date of birth, gender, age<br />
                &bull; C2 Contact information: email address, phone number<br />
                &bull; C3 Government identifiers: Aadhaar, PAN, passport, voter ID, driving licence<br />
                &bull; C4 Financial information: bank account, IFSC, card number, UPI ID<br />
                &bull; C5 Location / address: postal address, PIN code, geo-coordinates<br />
                Fields outside these classes are labelled not personal data.
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <span className="empty-icon"><Database size={21} /></span>
              <h3>No source selected</h3>
              <p>Select a data source from the wizard to inspect details.</p>
            </div>
          )}

          {/* Real-Time Scan Result Callout */}
          {result && (
            <div
              style={{
                marginTop: 20,
                padding: 18,
                background: "#13231F",
                border: "1px solid #285346",
                borderRadius: 6,
                color: "#AED7C4",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <Check size={18} style={{ color: "#63B79B" }} />
                <b style={{ fontSize: 13, color: "#F2F4FA" }}>Scan Completed Successfully</b>
              </div>
              <p style={{ fontSize: 11, color: "#C0E0D1", margin: "0 0 14px", lineHeight: 1.6 }}>
                Scan #{result.id} inspected <strong>{result.inspected_columns}</strong> columns across{" "}
                <strong>{result.rows_sampled}</strong> sample rows. Detected{" "}
                <strong>{result.findings}</strong> candidate personal data field(s).
              </p>
              <div style={{ display: "flex", gap: 10 }}>
                <Link href="/inventory" className="button button-small">
                  <ClipboardCheck size={14} /> Open Inventory
                </Link>
                <Link href="/review" className="button button-small button-outline">
                  Review Findings &rarr;
                </Link>
              </div>
            </div>
          )}
        </section>
      </div>

      <div className="disclaimer-line">
        <ShieldCheck size={15} />
        Discovery scans produce technical candidate evidence for human review. Raw sample rows are dropped immediately after regex classification.
      </div>
    </>
  );
}

export default function ScannerPage() {
  return (
    <WorkspaceShell title="Discovery Scanner">
      <Suspense fallback={<div>Loading scanner configuration…</div>}>
        <ScannerInner />
      </Suspense>
    </WorkspaceShell>
  );
}

