"use client";
import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  Check,
  FileSpreadsheet,
  FileUp,
  RefreshCw,
  ShieldCheck,
  Table,
  UploadCloud,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { WorkspaceShell } from "@/components/workspace-shell";
import { api, download, Metric } from "@/lib/api";

type EvaluationData = {
  dataset: string;
  synthetic: boolean;
  rule_version: string;
  sample_count?: number;
  classes: Metric[];
  macro?: {
    precision: number;
    recall: number;
    f1: number;
  };
  micro?: {
    precision: number;
    recall: number;
    f1: number;
  };
  confusion_matrix?: Record<string, Record<string, number>>;
};

export default function EvaluationPage() {
  const [data, setData] = useState<EvaluationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [customFile, setCustomFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);

  function loadEvaluation() {
    setLoading(true);
    api<EvaluationData>("/evaluation")
      .then((res) => {
        setData(res);
        setError("");
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    queueMicrotask(() => { void loadEvaluation(); });
  }, []);

  async function handleUploadCustomDataset(e: FormEvent) {
    e.preventDefault();
    if (!customFile) return;

    setBusy(true);
    setError("");
    setSuccess("");

    try {
      const formData = new FormData();
      formData.append("file", customFile);
      const res = await api<EvaluationData>("/evaluation/custom", {
        method: "POST",
        body: formData,
      });
      setData(res);
      setSuccess(`Evaluated custom dataset "${res.dataset}" successfully against active rule engine.`);
      setCustomFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Custom evaluation failed.");
    } finally {
      setBusy(false);
    }
  }

  const metrics = data?.classes || [];
  const chartData = metrics.map((m) => ({
    name: m.class_code,
    fullName: m.class_name,
    precision: m.precision === null ? 0 : Math.round(m.precision * 100),
    recall: m.recall === null ? 0 : Math.round(m.recall * 100),
    f1: m.f1 === null ? 0 : Math.round(m.f1 * 100),
  }));

  const confusionRows = data?.confusion_matrix ? Object.keys(data.confusion_matrix) : [];

  return (
    <WorkspaceShell title="Evaluation Center &amp; Quality Metrics">
      <div className="content-heading">
        <div>
          <span className="eyebrow">EMPIRICAL RULE EVALUATION</span>
          <h2>Measure Discovery Precision, Recall &amp; F1</h2>
          <p>
            Evaluation metrics are calculated from independently labelled test cases. Upload your team&apos;s verification datasets to compute empirical accuracy and confusion matrices without fabrication.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="button button-outline button-small" onClick={loadEvaluation} disabled={loading}>
            <RefreshCw size={14} className={loading ? "spin" : ""} /> Reset to Standard Fixture
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

      {/* Dataset Context Banner */}
      <div className="evaluation-note">
        <span className="demo-icon"><Activity size={18} /></span>
        <p>
          <b>Evaluation Dataset:</b> {data?.dataset || "Loading test fixture…"}{" "}
          {data?.sample_count ? `(${data.sample_count} labelled test cases)` : ""} &bull;{" "}
          <span style={{ color: "#AED7C4" }}>Ground truth verified</span>.
        </p>
        <span className="mono-cell">{data?.rule_version || "privexis-rules/v1.0"}</span>
      </div>

      {/* Macro & Micro Summary Cards */}
      <div className="metrics-grid">
        <article className="metric-card">
          <span>Macro Average F1</span>
          <strong style={{ color: "#9B83E8" }}>
            {data?.macro ? `${(data.macro.f1 * 100).toFixed(1)}%` : "—"}
          </strong>
          <small>Unweighted class mean</small>
        </article>
        <article className="metric-card">
          <span>Macro Precision</span>
          <strong style={{ color: "#63B79B" }}>
            {data?.macro ? `${(data.macro.precision * 100).toFixed(1)}%` : "—"}
          </strong>
          <small>TP / (TP + FP) across classes</small>
        </article>
        <article className="metric-card">
          <span>Macro Recall</span>
          <strong style={{ color: "#D7AD62" }}>
            {data?.macro ? `${(data.macro.recall * 100).toFixed(1)}%` : "—"}
          </strong>
          <small>TP / (TP + FN) across classes</small>
        </article>
        <article className="metric-card">
          <span>Micro Average F1</span>
          <strong style={{ color: "#F2F4FA" }}>
            {data?.micro ? `${(data.micro.f1 * 100).toFixed(1)}%` : "—"}
          </strong>
          <small>Global aggregated instances</small>
        </article>
      </div>

      {/* Chart Panel */}
      <section className="panel chart-panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">PER CLASS / PERCENTAGE</span>
            <h3>Precision, Recall &amp; F1 Comparison</h3>
          </div>
          <div className="chart-legend">
            <span><i style={{ background: "#9B83E8" }} /> Precision</span>
            <span><i style={{ background: "#777E8E" }} /> Recall</span>
            <span><i style={{ background: "#63B79B" }} /> F1 Score</span>
          </div>
        </div>

        {chartData.length > 0 ? (
          <div className="chart-wrap" style={{ height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 12, right: 12, left: -14, bottom: 4 }}>
                <CartesianGrid stroke="#292E3B" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: "#A1A8B8", fontSize: 11 }} axisLine={{ stroke: "#292E3B" }} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: "#81899A", fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ background: "#171B27", border: "1px solid #292E3B", borderRadius: 6, color: "#F2F4FA", fontSize: 11 }}
                  formatter={(v, name) => [`${v}%`, name]}
                />
                <Bar dataKey="precision" name="Precision" fill="#9B83E8" radius={[3, 3, 0, 0]} maxBarSize={22} />
                <Bar dataKey="recall" name="Recall" fill="#777E8E" radius={[3, 3, 0, 0]} maxBarSize={22} />
                <Bar dataKey="f1" name="F1 Score" fill="#63B79B" radius={[3, 3, 0, 0]} maxBarSize={22} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="empty-state">Loading chart…</div>
        )}
      </section>

      {/* Confusion Matrix & Detailed Counts Table */}
      <div className="split-panels">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">STATISTICAL BREAKDOWN</span>
              <h3>Per-Class Performance</h3>
            </div>
          </div>

          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Class</th>
                  <th>TP</th>
                  <th>FP</th>
                  <th>FN</th>
                  <th>Precision</th>
                  <th>Recall</th>
                  <th>F1</th>
                </tr>
              </thead>
              <tbody>
                {metrics.map((m) => (
                  <tr key={m.class_code}>
                    <td>
                      <span className="class-chip">{m.class_code}</span> <strong>{m.class_name}</strong>
                    </td>
                    <td>{m.tp}</td>
                    <td>{m.fp}</td>
                    <td>{m.fn}</td>
                    <td>{m.precision === null ? "N/A" : `${(m.precision * 100).toFixed(1)}%`}</td>
                    <td>{m.recall === null ? "N/A" : `${(m.recall * 100).toFixed(1)}%`}</td>
                    <td style={{ color: "#63B79B", fontWeight: 700 }}>
                      {m.f1 === null ? "N/A" : `${(m.f1 * 100).toFixed(1)}%`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="panel-note">
            TP = True Positive. FP = False Positive. FN = False Negative. F1 = 2 &times; (Precision &times; Recall) / (Precision + Recall).
          </p>
        </section>

        {/* Custom Dataset Upload Section */}
        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">EMPIRICAL BENCHMARK</span>
              <h3>Upload Labelled Test Dataset</h3>
            </div>
          </div>
          <p style={{ color: "#A1A8B8", fontSize: 11, lineHeight: 1.7, margin: "0 0 14px" }}>
            Benchmark against your own curated test cases. Upload a CSV with columns: <code style={{ color: "#D4C7F2" }}>column_name</code>, <code style={{ color: "#D4C7F2" }}>sample_value</code>, and <code style={{ color: "#D4C7F2" }}>true_class</code> (C1..C5 or blank for non-PII).
          </p>

          <form onSubmit={handleUploadCustomDataset} className="upload-form" style={{ flexDirection: "column", alignItems: "stretch" }}>
            <label className="file-drop" style={{ minHeight: 70 }}>
              <UploadCloud size={20} />
              <span>
                <b>{customFile ? customFile.name : "Select evaluation benchmark CSV"}</b>
                <small>{customFile ? `${(customFile.size / 1024).toFixed(1)} KB` : "CSV with ground truth labels"}</small>
              </span>
              <input
                type="file"
                accept=".csv,text/csv"
                onChange={(e: ChangeEvent<HTMLInputElement>) => setCustomFile(e.target.files?.[0] || null)}
                required
              />
            </label>
            <button className="button" disabled={!customFile || busy}>
              {busy ? "Evaluating Dataset…" : "Run Custom Evaluation Benchmark"}
            </button>
          </form>
        </section>
      </div>

      <div className="disclaimer-line">
        <ShieldCheck size={15} />
        Evaluation results describe performance on the designated fixture only. They do not predict real-world accuracy across arbitrary external distributions.
      </div>
    </WorkspaceShell>
  );
}

