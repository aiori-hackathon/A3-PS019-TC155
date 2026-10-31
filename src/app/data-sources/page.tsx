"use client";
import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Check,
  Database,
  FileSpreadsheet,
  FileUp,
  Layers,
  Lock,
  RefreshCw,
  Search,
  Server,
  Table,
  Trash2,
  UploadCloud,
  X,
} from "lucide-react";
import { WorkspaceShell } from "@/components/workspace-shell";
import { api, Source } from "@/lib/api";

type TableInfo = {
  table_name: string;
  columns: Array<{ name: string; type: string }>;
};

type SchemaResponse = {
  source_id: number;
  source: string;
  kind: string;
  tables: TableInfo[];
};
type SampleDataset = { id: string; name: string; class_code: string; class_name: string; kind: "csv" | "sqlite"; description: string };

export default function DataSourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [selectedSchema, setSelectedSchema] = useState<SchemaResponse | null>(null);
  const [schemaLoading, setSchemaLoading] = useState(false);
  const [samples, setSamples] = useState<SampleDataset[]>([]);
  const [sampleBusy, setSampleBusy] = useState("");

  function loadSources() {
    api<Source[]>("/sources")
      .then((data) => setSources(data))
      .catch((err) => setError(err.message));
  }

  useEffect(() => {
    loadSources();
    api<SampleDataset[]>("/samples").then(setSamples).catch((err) => setError(err.message));
  }, []);

  async function addAndScanSample(sample: SampleDataset) {
    setSampleBusy(sample.id);
    setError("");
    setSuccess("");
    try {
      const source = await api<{ id: number; name: string }>(`/samples/${sample.id}/load`, { method: "POST" });
      const scan = await api<{ status: string; findings: number; error?: string }>(`/sources/${source.id}/scan?sample_limit=500`, { method: "POST" });
      if (scan.status !== "completed") throw new Error(scan.error || "The sample scan failed.");
      setSuccess(`${source.name} scanned successfully: ${scan.findings} candidate finding(s).`);
      loadSources();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load and scan the sample.");
    } finally {
      setSampleBusy("");
    }
  }

  async function handleUpload(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setBusy(true);
    setError("");
    setSuccess("");

    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await api<{ id: number; name: string; kind: string }>("/sources/upload", {
        method: "POST",
        body: formData,
      });
      setSuccess(`Data source "${res.name}" registered successfully. You can now inspect schema or run discovery.`);
      setFile(null);
      loadSources();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  async function removeSource(id: number, name: string) {
    if (!window.confirm(`Are you sure you want to disconnect and delete data source "${name}"? Stored upload and associated scan findings will be deleted.`)) {
      return;
    }
    setError("");
    setSuccess("");
    try {
      await api(`/sources/${id}`, { method: "DELETE" });
      setSuccess(`Source "${name}" disconnected successfully.`);
      if (selectedSchema?.source_id === id) setSelectedSchema(null);
      loadSources();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete source.");
    }
  }

  async function inspectSchema(sourceId: number) {
    setSchemaLoading(true);
    setError("");
    try {
      const schema = await api<SchemaResponse>(`/sources/${sourceId}/schema`);
      setSelectedSchema(schema);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not inspect source schema.");
    } finally {
      setSchemaLoading(false);
    }
  }

  return (
    <WorkspaceShell title="Data Source Registry">
      <div className="content-heading">
        <div>
          <span className="eyebrow">STRUCTURED SOURCE REPOSITORY</span>
          <h2>Register and inspect repositories safely.</h2>
          <p>
            Connect UTF-8 CSV datasets and SQLite databases for personal data discovery. Scans are local and bounded; SQLite databases are opened exclusively in read-only mode (<code style={{ color: "#D4C7F2" }}>mode=ro</code>).
          </p>
        </div>
        <Link href="/scanner" className="button button-small">
          Go to Discovery Scanner <ArrowRight size={14} />
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

      {/* Upload Ingestion Section */}
      <section className="panel upload-panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">INGESTION &amp; VALIDATION</span>
            <h3>Connect New Structured Source</h3>
          </div>
          <span className="limit-note">Maximum 15 MB &bull; UTF-8 / SQLite 3</span>
        </div>

        <form onSubmit={handleUpload} className="upload-form">
          <label className="file-drop">
            <UploadCloud size={24} />
            <span>
              <b>{file ? file.name : "Select or drag & drop CSV or SQLite database"}</b>
              <small>
                {file ? `${(file.size / 1024).toFixed(1)} KB selected` : "Supported formats: .csv, .db, .sqlite, .sqlite3"}
              </small>
            </span>
            <input
              type="file"
              accept=".csv,.db,.sqlite,.sqlite3,text/csv,application/vnd.sqlite3"
              onChange={(e: ChangeEvent<HTMLInputElement>) => setFile(e.target.files?.[0] || null)}
              required
            />
          </label>
          <button className="button" disabled={!file || busy}>
            <FileUp size={16} /> {busy ? "Ingesting & Validating…" : "Register Source"}
          </button>
        </form>
        <p className="privacy-hint">
          Safety guarantee: SQLite connections are strictly read-only. Bounded row sampling is used during discovery, and raw record values are never persisted.
        </p>
      </section>

      <section className="panel sample-panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">REPRODUCIBLE SYNTHETIC FIXTURES</span>
            <h3>Try one of the 10 sample files</h3>
          </div>
          <span className="limit-note">Two formats for each of the five classes</span>
        </div>
        <div className="sample-grid">
          {samples.map((sample) => (
            <article className="sample-card" key={sample.id}>
              <span className="class-chip">{sample.class_code}</span>
              <div><b>{sample.class_name}</b><small>{sample.kind.toUpperCase()} · 20 synthetic records</small></div>
              <p>{sample.description}</p>
              <button className="button button-small button-outline" onClick={() => addAndScanSample(sample)} disabled={!!sampleBusy || busy}>
                {sampleBusy === sample.id ? <><RefreshCw size={13} className="spin" /> Scanning…</> : <><FileUp size={13} /> Add &amp; run scan</>}
              </button>
            </article>
          ))}
        </div>
        <p className="privacy-hint">All sample values are synthetic. The same scanner handles uploaded files and these examples.</p>
      </section>

      {/* Registered Data Sources */}
      <section className="panel">
        <div className="panel-heading">
          <div>
            <span className="eyebrow">ACTIVE REPOSITORIES</span>
            <h3>Registered Sources <span className="count-badge">{sources.length}</span></h3>
          </div>
          <button className="icon-button" onClick={loadSources} title="Refresh sources" aria-label="Refresh sources">
            <RefreshCw size={15} />
          </button>
        </div>

        {sources.length > 0 ? (
          <div className="source-list">
            {sources.map((src) => (
              <div className="source-row" key={src.id}>
                <div className="source-type-icon">
                  {src.kind === "sqlite" ? <Database size={18} /> : <FileSpreadsheet size={18} />}
                </div>
                <div className="source-copy">
                  <b>{src.name}</b>
                  <small>
                    {src.kind.toUpperCase()} Repository &bull; {(src.size_bytes / 1024).toFixed(1)} KB &bull; Connected {new Date(src.created_at).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" })}
                  </small>
                </div>
                <span className="status-pill status-ready">Ready for scan</span>
                <button
                  className="button button-small button-outline"
                  onClick={() => inspectSchema(src.id)}
                  disabled={schemaLoading}
                  style={{ gap: 6 }}
                >
                  <Table size={13} /> Inspect Schema
                </button>
                <Link href={`/scanner?source=${src.id}`} className="button button-small" style={{ gap: 6 }}>
                  Scan <ArrowRight size={13} />
                </Link>
                <button
                  className="icon-button danger-icon"
                  onClick={() => removeSource(src.id, src.name)}
                  title={`Disconnect ${src.name}`}
                  aria-label={`Disconnect ${src.name}`}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <span className="empty-icon"><Database size={21} /></span>
            <h3>No data sources registered</h3>
            <p>Upload a CSV file or SQLite database above to begin personal data discovery.</p>
          </div>
        )}
      </section>

      {/* Schema Preview Modal / Drawer */}
      {selectedSchema && (
        <section className="panel" style={{ border: "1px solid #483E63", background: "#13141F" }}>
          <div className="panel-heading">
            <div>
              <span className="eyebrow">SAFE SCHEMA PREVIEW</span>
              <h3>Structure for {selectedSchema.source}</h3>
            </div>
            <button className="icon-button" onClick={() => setSelectedSchema(null)} aria-label="Close schema">
              <X size={18} />
            </button>
          </div>
          <p style={{ color: "#A1A8B8", fontSize: 11, margin: "0 0 16px" }}>
            Discovered {selectedSchema.tables.length} table/scope(s). No row values are shown in schema previews.
          </p>

          <div style={{ display: "grid", gap: 16 }}>
            {selectedSchema.tables.map((t, idx) => (
              <div key={idx} style={{ background: "#0D0F16", border: "1px solid #252A36", borderRadius: 6, padding: 16 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                  <Table size={15} style={{ color: "#9B83E8" }} />
                  <b style={{ fontSize: 13 }}>{t.table_name ? `Table: ${t.table_name}` : "CSV File Header Scope"}</b>
                  <span className="count-badge">{t.columns.length} columns</span>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 8 }}>
                  {t.columns.map((col, cIdx) => (
                    <div key={cIdx} style={{ padding: "8px 12px", background: "#171B27", border: "1px solid #282D3B", borderRadius: 4 }}>
                      <code style={{ fontSize: 11, color: "#F2F4FA", display: "block" }}>{col.name}</code>
                      <small style={{ color: "#818897", fontSize: 9 }}>{col.type}</small>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 16, display: "flex", justifyContent: "flex-end", gap: 10 }}>
            <Link href={`/scanner?source=${selectedSchema.source_id}`} className="button button-small">
              Start Scan on This Source <ArrowRight size={13} />
            </Link>
          </div>
        </section>
      )}

      {/* Planned Enterprise Connectors */}
      <section className="panel" style={{ marginTop: 24 }}>
        <div className="panel-heading">
          <div>
            <span className="eyebrow">ROADMAP &amp; FUTURE INTEGRATIONS</span>
            <h3>Enterprise Relational Connectors</h3>
          </div>
          <span style={{ fontSize: 10, color: "#818897" }}>Specifications Defined</span>
        </div>
        <p style={{ color: "#A1A8B8", fontSize: 11, lineHeight: 1.7, margin: "0 0 16px" }}>
          Production deployments can configure read-only database credentials for relational database discovery. The scanner inspects target table structures using parameterized queries with row limits.
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 14 }}>
          <div style={{ padding: 16, background: "#12151F", border: "1px solid #242936", borderRadius: 6 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
              <Layers size={17} style={{ color: "#9B83E8" }} />
              <b style={{ fontSize: 13 }}>PostgreSQL Connector</b>
            </div>
            <p style={{ color: "#858C9A", fontSize: 10, lineHeight: 1.6, margin: 0 }}>
              Read-only connection pool to scan PostgreSQL schemas, partition catalogs, and table columns with sample row caps.
            </p>
          </div>

          <div style={{ padding: 16, background: "#12151F", border: "1px solid #242936", borderRadius: 6 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
              <Server size={17} style={{ color: "#9B83E8" }} />
              <b style={{ fontSize: 13 }}>MySQL Connector</b>
            </div>
            <p style={{ color: "#858C9A", fontSize: 10, lineHeight: 1.6, margin: 0 }}>
              Information schema inspection for MySQL 8.0+ with bounded query execution and sensitive field heuristics.
            </p>
          </div>

          <div style={{ padding: 16, background: "#12151F", border: "1px solid #242936", borderRadius: 6 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
              <Lock size={17} style={{ color: "#9B83E8" }} />
              <b style={{ fontSize: 13 }}>Microsoft SQL Server</b>
            </div>
            <p style={{ color: "#858C9A", fontSize: 10, lineHeight: 1.6, margin: 0 }}>
              Read-only catalog profiling across user databases and table schemas with encrypted TLS transports.
            </p>
          </div>
        </div>
      </section>
    </WorkspaceShell>
  );
}

