"use client";
import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Check,
  CheckCircle2,
  Code2,
  FlaskConical,
  Play,
  RefreshCw,
  Search,
  ShieldCheck,
  Sliders,
  Terminal,
} from "lucide-react";
import { WorkspaceShell } from "@/components/workspace-shell";
import { api, RuleDefinition } from "@/lib/api";

type RulesResponse = {
  version: string;
  classes: Record<string, string>;
  descriptions: Record<string, string>;
  enabled_classes: string[];
  rules: RuleDefinition[];
};

type RuleTestResult = {
  column_name: string;
  sample_value: string;
  matched: boolean;
  label: string;
  matches: Array<{
    data_class: string;
    class_name: string;
    confidence: string;
    rule_id: string;
    evidence: string;
  }>;
};

export default function RulesPage() {
  const [data, setData] = useState<RulesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [enabledClasses, setEnabledClasses] = useState<string[]>(["C1", "C2", "C3", "C4", "C5"]);
  const [saving, setSaving] = useState(false);
  const [saveNotice, setSaveNotice] = useState("");

  // Sandbox Tester State
  const [testCol, setTestCol] = useState("user_email_address");
  const [testVal, setTestVal] = useState("alex.sample@example.com");
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<RuleTestResult | null>(null);

  function loadRules() {
    setLoading(true);
    api<RulesResponse>("/rules")
      .then((res) => {
        setData(res);
        setEnabledClasses(res.enabled_classes);
        setError("");
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    queueMicrotask(() => {
      void loadRules();
      void runTest("user_email_address", "alex.sample@example.com");
    });
  }, []);

  async function runTest(column: string, value: string) {
    setTesting(true);
    try {
      const res = await api<RuleTestResult>("/rules/test", {
        method: "POST",
        body: JSON.stringify({ column_name: column, sample_value: value }),
      });
      setTestResult(res);
    } catch {
      /* Keep fallback */
    } finally {
      setTesting(false);
    }
  }

  function handleTestSubmit(e: FormEvent) {
    e.preventDefault();
    if (!testCol.trim()) return;
    runTest(testCol.trim(), testVal.trim());
  }

  async function saveConfiguration() {
    if (enabledClasses.length === 0) {
      setError("Enable at least one class rule before saving.");
      return;
    }
    setSaving(true);
    setError("");
    setSaveNotice("");
    try {
      await api("/rules/config", {
        method: "PUT",
        body: JSON.stringify({ enabled_classes: enabledClasses }),
      });
      setSaveNotice("Evidence checklist saved. New scans will use these enabled class rules.");
      loadRules();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the evidence checklist.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <WorkspaceShell title="Detection Rules &amp; Classification Engine">
      <div className="content-heading">
        <div>
          <span className="eyebrow">REGULATORY DATA TAXONOMY</span>
          <h2>Configured Detection Rules &amp; Sandbox</h2>
          <p>
            Inspect the active pattern heuristics, regex format validators, and confidence algorithms grouping candidate personal data into the 5 core privacy classes.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <span className="count-badge" style={{ padding: "6px 12px", height: "auto" }}>
            Engine {data?.version || "loading"}
          </span>
        </div>
      </div>

      {error && <div className="notice notice-error" role="alert">{error}</div>}
      {saveNotice && <div className="notice notice-success" role="status">{saveNotice}</div>}

      <section className="panel" style={{ marginBottom: 24 }}>
        <div className="panel-heading">
          <div>
            <span className="eyebrow">CONFIGURABLE EVIDENCE CHECKLIST</span>
            <h3>Choose the class rules used in scans</h3>
          </div>
          <button className="button button-small" type="button" onClick={saveConfiguration} disabled={saving || loading}>
            {saving ? "Saving…" : "Save checklist"}
          </button>
        </div>
        <p className="panel-note">All five rules are enabled by default. Turn off a class to exclude its detections from new scans in this workspace. The evaluation page always reports all five classes.</p>
        <div className="class-list">
          {data?.classes && Object.entries(data.classes).map(([code, name]) => (
            <label className="settings-field" key={code} style={{ justifyContent: "flex-start", gap: 12, cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={enabledClasses.includes(code)}
                disabled={saving || loading}
                onChange={(event) => setEnabledClasses((current) => event.target.checked ? [...current, code] : current.filter((item) => item !== code))}
              />
              <span>{code}</span>
              <b>{name}</b>
              <small style={{ marginLeft: "auto" }}>{data.descriptions[code]}</small>
            </label>
          ))}
        </div>
      </section>

      {/* Interactive Rule Sandbox / Tester */}
      <section className="panel" style={{ border: "1px solid #483E63", background: "#11131E", marginBottom: 24 }}>
        <div className="panel-heading">
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <FlaskConical size={18} style={{ color: "#9B83E8" }} />
            <div>
              <span className="eyebrow">REAL-TIME CLASSIFIER TESTER</span>
              <h3>Rule Sandbox &amp; Verification Terminal</h3>
            </div>
          </div>
          <span style={{ fontSize: 9, color: "#9B83E8" }}>Zero Persistent Storage</span>
        </div>
        <p style={{ color: "#A1A8B8", fontSize: 11, margin: "0 0 16px" }}>
          Simulate detection by entering an arbitrary field identifier and optional bounded sample value to inspect rule matching explanations in real-time.
        </p>

        <form onSubmit={handleTestSubmit} style={{ display: "grid", gridTemplateColumns: "1fr 1fr auto", gap: 12, alignItems: "end" }}>
          <label style={{ display: "grid", gap: 6, fontSize: 10, fontWeight: 700, color: "#C5C9D4" }}>
            Candidate Column / Field Name
            <input
              required
              value={testCol}
              onChange={(e) => setTestCol(e.target.value)}
              placeholder="e.g. email_address, aadhaar_number, postal_address"
              style={{ background: "#171B27", border: "1px solid #282D3B", borderRadius: 4, height: 40, padding: "0 10px", color: "#F2F4FA", fontSize: 11 }}
            />
          </label>

          <label style={{ display: "grid", gap: 6, fontSize: 10, fontWeight: 700, color: "#C5C9D4" }}>
            Sample Value Format (Optional)
            <input
              value={testVal}
              onChange={(e) => setTestVal(e.target.value)}
              placeholder="e.g. 1990-05-12, +1 555-0199"
              style={{ background: "#171B27", border: "1px solid #282D3B", borderRadius: 4, height: 40, padding: "0 10px", color: "#F2F4FA", fontSize: 11 }}
            />
          </label>

          <button className="button" type="submit" disabled={testing} style={{ height: 40 }}>
            {testing ? "Testing…" : <><Play size={13} /> Run Rule Test</>}
          </button>
        </form>

        {/* Live Match Output */}
        {testResult && (
          <div style={{ marginTop: 16, padding: 14, background: "#0A0D15", border: "1px solid #242938", borderRadius: 6 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: testResult.matched ? "#63B79B" : "#D7AD62" }} />
                <b style={{ fontSize: 12, color: testResult.matched ? "#9FD0B8" : "#E0B77D" }}>
                  {testResult.matched ? `MATCH CONFIRMED (${testResult.matches.length} detection rule)` : "NO RULE MATCH (not personal data)"}
                </b>
              </div>
              <small style={{ color: "#818897", fontSize: 9 }}>Input: {testResult.column_name}</small>
            </div>

            {testResult.matched ? (
              <div style={{ display: "grid", gap: 8 }}>
                {testResult.matches.map((m, idx) => (
                  <div key={idx} style={{ padding: 10, background: "#151822", border: "1px solid #282D3B", borderRadius: 4, fontSize: 11 }}>
                    <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
                      <span className="class-chip">{m.data_class}</span>
                      <strong style={{ color: "#F2F4FA" }}>{m.class_name}</strong>
                      <span style={{ marginLeft: "auto", color: m.confidence === "high" ? "#63B79B" : "#D7AD62", fontSize: 10, fontWeight: 700 }}>
                        {m.confidence.toUpperCase()} CONFIDENCE
                      </span>
                    </div>
                    <p style={{ margin: 0, color: "#A1A8B8", fontSize: 10 }}>{m.evidence}</p>
                    <code style={{ fontSize: 9, color: "#C4B4FA", display: "block", marginTop: 4 }}>Rule ID: {m.rule_id}</code>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: "#858C9A", fontSize: 11, margin: 0 }}>
                This field matches none of the five configured classes and is labelled not personal data.
              </p>
            )}
          </div>
        )}
      </section>

      {/* The 5 Canonical Privacy Data Classes */}
      <section className="panel" style={{ marginBottom: 24 }}>
        <div className="panel-heading">
          <div>
            <span className="eyebrow">FIVE PERSONAL-DATA CLASSES</span>
            <h3>Personal Data Taxonomy</h3>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 14 }}>
          {data?.classes && Object.entries(data.classes).map(([code, name]) => (
            <div key={code} style={{ padding: 16, background: "#141722", border: "1px solid #262B3A", borderRadius: 6 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                <span className="class-chip">{code}</span>
                <span style={{ fontSize: 9, color: "#63B79B", display: "flex", alignItems: "center", gap: 4 }}>
                  <CheckCircle2 size={11} /> {enabledClasses.includes(code) ? "Enabled" : "Disabled"}
                </span>
              </div>
              <b style={{ fontSize: 13, display: "block", marginBottom: 6 }}>{name}</b>
              <p style={{ color: "#858C9A", fontSize: 10, lineHeight: 1.6, margin: 0 }}>
                {data.descriptions?.[code] || "Privacy protection class"}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Rules Catalog Table */}
      <section className="panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">RULE CATALOG</span>
            <h3>Active Detection Rules <span className="count-badge">{data?.rules?.length || 0}</span></h3>
          </div>
        </div>

        {data?.rules && data.rules.length > 0 ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Rule Name</th>
                  <th>Class</th>
                  <th>Pattern Specification</th>
                  <th>Format Validator</th>
                  <th>Confidence</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {data.rules.map((r) => (
                  <tr key={r.id}>
                    <td>
                      <strong>{r.name}</strong>
                      <small style={{ color: "#818897", display: "block", fontSize: 8 }}>ID: {r.id}</small>
                    </td>
                    <td>
                      <span className="class-chip">{r.data_class}</span> {r.class_name}
                    </td>
                    <td>
                      <code className="mono-cell" style={{ color: "#D4C7F2" }}>{r.pattern}</code>
                    </td>
                    <td>
                      <small style={{ color: "#A1A8B8" }}>{r.format_validator || "Column Name Match"}</small>
                    </td>
                    <td>
                      <span style={{ color: r.confidence === "high" ? "#63B79B" : "#D7AD62", fontWeight: 700, fontSize: 10 }}>
                        {r.confidence.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <span className={`status-pill ${r.enabled ? "status-ready" : "status-failed"}`}>{r.enabled ? "Enabled" : "Disabled"}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <span className="empty-icon"><Sliders size={21} /></span>
            <h3>Loading rules catalog…</h3>
          </div>
        )}
      </section>

      <div className="disclaimer-line">
        <ShieldCheck size={15} />
        Privexis rules are deterministic, explainable, and reproducible without relying on unexplainable black-box models.
      </div>
    </WorkspaceShell>
  );
}

