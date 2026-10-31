import Link from "next/link";
import { ArrowRight, ArrowUpRight, Check, Database, FileSpreadsheet, Fingerprint, Lock, Shield, ScanSearch, ShieldCheck, Layers, FileText, Activity } from "lucide-react";
import { PublicNav } from "@/components/public-nav";
import { PublicFooter } from "@/components/public-footer";

export default function Home() {
  return (
    <>
      <PublicNav />
      <main>
        {/* Hero Section */}
        <section className="hero page-width">
          <div className="hero-copy">
            <div className="hero-kicker">
              <span className="kicker-line" /> PERSONAL DATA DISCOVERY & PRIVACY EVIDENCE
            </div>
            <h1>
              Discover Personal Data.<br />
              <em>Build Privacy Evidence.</em>
            </h1>
            <p className="hero-lede">
              Privexis inspects structured data sources to discover candidate personal-data fields, maps declared purpose and retention schedules, and generates verifiable technical evidence trails with human review.
            </p>
            <div className="hero-actions">
              <Link href="/data-sources" className="button">
                Get started <ArrowRight size={16} />
              </Link>
              <Link href="/scanner" className="button button-outline">
                Start a scan <ArrowRight size={16} />
              </Link>
              <Link href="/how-it-works" className="text-link">
                How it works <ArrowUpRight size={15} />
              </Link>
            </div>
            <div className="hero-proof">
              <span><Check size={14} /> Read-only SQLite inspection</span>
              <span><Check size={14} /> Bounded, local sample processing</span>
              <span><Check size={14} /> Five personal-data classes</span>
            </div>
          </div>

          <div className="hero-visual" aria-label="Privexis evidence workbench preview">
            <div className="visual-grid" />
            <div className="evidence-window">
              <div className="window-bar">
                <div className="window-brand">
                  <span className="tiny-mark">P</span> privexis <span className="window-path">/ evidence / review-queue</span>
                </div>
                <span className="window-status"><i /> VERIFIED EVIDENCE</span>
              </div>
              <div className="window-content">
                <div className="window-rail">
                  <b>NAVIGATION</b>
                  <span className="rail-selected">◈ &nbsp; Candidates</span>
                  <span>⌘ &nbsp; Sources</span>
                  <span>▤ &nbsp; Rules</span>
                  <span>◷ &nbsp; Gaps</span>
                  <span>⚙ &nbsp; Audit</span>
                </div>
                <div className="window-main">
                  <div className="window-heading">
                    <div>
                      <small>FINDING / PX-00418</small>
                      <h3>customer_contact_email</h3>
                    </div>
                  <span className="candidate-badge">Contact information · C2</span>
                  </div>
                  <div className="window-meta">
                    <div><small>DATA SOURCE</small><b>member_registry.csv</b></div>
                    <div><small>DETECTION RULE</small><b>c2_contact_v2 (High Confidence)</b></div>
                  </div>
                  <div className="evidence-callout">
                    <span className="evidence-icon"><Fingerprint size={16} /></span>
                    <div>
                      <b>Technical Detection Rationale</b>
                      <p>Header matches configured email identifier patterns. Sample formatting conforms to RFC 5322. Raw values are not retained.</p>
                    </div>
                  </div>
                  <div className="review-line">
                    <div>
                      <span className="review-avatar">RV</span>
                      <span>Awaiting human review</span>
                    </div>
                    <button aria-label="Review finding action">
                      Confirm Candidate <ArrowRight size={13} />
                    </button>
                  </div>
                  <div className="mini-table">
                    <span>Declared Business Purpose</span>
                    <span style={{ color: "#9FD0B8", fontSize: "8px" }}>Account Management &amp; Billing</span>
                    <span>Retention Schedule</span>
                    <span style={{ color: "#9FD0B8", fontSize: "8px" }}>7 Years Statutory</span>
                  </div>
                </div>
              </div>
              <div className="window-foot">
                <span>RULE SET <b>privexis-rules/v2.0</b></span>
                <span>TECHNICAL EVIDENCE <b>·</b> HUMAN AUDIT DECISION</span>
              </div>
            </div>
            <div className="floating-note">
              <span className="floating-dot" />
              <span><b>Evidence, not an automated verdict.</b><small>Decisions stay in human control.</small></span>
            </div>
          </div>
        </section>

        {/* Trust Band */}
        <section className="trust-band">
          <div className="page-width trust-inner">
            <span className="trust-label">PLATFORM HIGHLIGHTS &amp; FOUNDATIONAL PRINCIPLES</span>
            <div className="trust-items">
              <span><Database size={15} /> Bounded Ingestion</span>
              <span><ScanSearch size={15} /> Explainable Classification</span>
              <span><FileText size={15} /> Declared Context Mapping</span>
              <span><ShieldCheck size={15} /> Auditable Human Review</span>
            </div>
          </div>
        </section>

        {/* How Privexis Works */}
        <section className="section page-width">
          <div className="section-heading">
            <div>
              <span className="eyebrow">WORKBENCH METHODOLOGY</span>
              <h2>Move from scattered fields<br />to an evidence trail.</h2>
            </div>
            <p>One unified workflow connects discovery to the governance context your privacy and compliance teams need.</p>
          </div>

          <div className="workflow-grid">
            <article className="workflow-step step-wide">
              <span className="step-num">01 / INGESTION &amp; PROFILING</span>
              <div className="step-icon"><Database size={20} /></div>
              <h3>Connect structured data sources.</h3>
              <p>Upload a CSV file or connect a SQLite database. Privexis inspects schemas safely and profiles bounded samples with read-only guarantees.</p>
              <Link href="/data-sources" className="subtle-arrow">Inspect sources <ArrowUpRight size={14} /></Link>
            </article>

            <article className="workflow-step">
              <span className="step-num">02 / DISCOVERY ENGINE</span>
              <div className="step-icon"><ScanSearch size={20} /></div>
              <h3>Explainable rule classification.</h3>
              <p>Five explainable classes cover personal identity, contact information, government identifiers, financial information, and location / address. Other fields are labelled not personal data.</p>
              <Link href="/rules" className="subtle-arrow">Explore rule catalog <ArrowUpRight size={14} /></Link>
            </article>

            <article className="workflow-step step-offset">
              <span className="step-num">03 / CONTEXT &amp; AUDIT</span>
              <div className="step-icon"><ShieldCheck size={20} /></div>
              <h3>Human review &amp; declared metadata.</h3>
              <p>Review candidates yourself, record a decision, and map declared purpose and retention. Missing metadata stays visible as an evidence gap.</p>
              <Link href="/review" className="subtle-arrow">Review workflow <ArrowUpRight size={14} /></Link>
            </article>
          </div>
        </section>

        {/* Supported Data Sources & Connectors */}
        <section className="section page-width" style={{ borderTop: "1px solid var(--line)" }}>
          <div className="section-heading">
            <div>
              <span className="eyebrow">SUPPORTED REPOSITORIES</span>
              <h2>Supported file formats.</h2>
            </div>
            <p>Designed for data privacy engineers who need offline-capable discovery without leaking sensitive values.</p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 16 }}>
            <div className="panel" style={{ padding: 24, margin: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
                <span style={{ width: 36, height: 36, borderRadius: 8, background: "#1B2234", display: "grid", placeItems: "center", color: "#9B83E8" }}>
                  <FileSpreadsheet size={18} />
                </span>
                <div>
                  <h3 style={{ margin: 0, fontSize: 14 }}>Delimited CSV Files</h3>
                  <small style={{ color: "#63B79B", fontSize: 9 }}>Available &bull; Local Profiling</small>
                </div>
              </div>
              <p style={{ color: "#A1A8B8", fontSize: 11, lineHeight: 1.7, margin: 0 }}>
                Upload UTF-8 CSV datasets up to 15 MB. Automatic deduplication of column headers and bounded row sampling up to 5,000 rows.
              </p>
            </div>

            <div className="panel" style={{ padding: 24, margin: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
                <span style={{ width: 36, height: 36, borderRadius: 8, background: "#1B2234", display: "grid", placeItems: "center", color: "#9B83E8" }}>
                  <Database size={18} />
                </span>
                <div>
                  <h3 style={{ margin: 0, fontSize: 14 }}>SQLite Databases</h3>
                  <small style={{ color: "#63B79B", fontSize: 9 }}>Available &bull; Read-Only Mode</small>
                </div>
              </div>
              <p style={{ color: "#A1A8B8", fontSize: 11, lineHeight: 1.7, margin: 0 }}>
                Direct ingestion of .db, .sqlite, and .sqlite3 databases. Opened exclusively with <code style={{ color: "#D4C7F2", fontSize: 10 }}>mode=ro</code> to guarantee source immutability.
              </p>
            </div>

            <div className="panel" style={{ padding: 24, margin: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
                <span style={{ width: 36, height: 36, borderRadius: 8, background: "#1B1825", display: "grid", placeItems: "center", color: "#777E8E" }}>
                  <Layers size={18} />
                </span>
                <div>
                  <h3 style={{ margin: 0, fontSize: 14 }}>PostgreSQL &amp; MySQL (not available)</h3>
                  <small style={{ color: "#D7AD62", fontSize: 9 }}>Not supported in this build</small>
                </div>
              </div>
              <p style={{ color: "#A1A8B8", fontSize: 11, lineHeight: 1.7, margin: 0 }}>
                Direct database connections are not available yet. Use a CSV export or SQLite file in this version.
              </p>
            </div>

            <div className="panel" style={{ padding: 24, margin: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
                <span style={{ width: 36, height: 36, borderRadius: 8, background: "#1B1825", display: "grid", placeItems: "center", color: "#777E8E" }}>
                  <Lock size={18} />
                </span>
                <div>
                  <h3 style={{ margin: 0, fontSize: 14 }}>SQL Server (not available)</h3>
                  <small style={{ color: "#D7AD62", fontSize: 9 }}>Not supported in this build</small>
                </div>
              </div>
              <p style={{ color: "#A1A8B8", fontSize: 11, lineHeight: 1.7, margin: 0 }}>
                Direct SQL Server connections are not available yet. Use a CSV export or SQLite file in this version.
              </p>
            </div>
          </div>
        </section>

        {/* Security & Transparency Section */}
        <section className="section page-width" style={{ borderTop: "1px solid var(--line)" }}>
          <div className="section-heading">
            <div>
              <span className="eyebrow">SECURITY ARCHITECTURE</span>
              <h2>Privacy minimization by design.</h2>
            </div>
            <p>Privexis itself handles privacy discovery, which is why defensive security controls are built into every layer.</p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 16 }}>
            <div className="panel" style={{ padding: 24, margin: 0 }}>
              <span className="eyebrow" style={{ color: "#9B83E8" }}>BROWSER-LOCAL WORKSPACES</span>
              <h3 style={{ fontSize: 15, margin: "8px 0 10px" }}>No login required</h3>
              <p style={{ color: "#A1A8B8", fontSize: 11, lineHeight: 1.8 }}>
                Each browser receives a random workspace key. Requests are isolated by that key and writes use an origin-bound CSRF token.
              </p>
            </div>

            <div className="panel" style={{ padding: 24, margin: 0 }}>
              <span className="eyebrow" style={{ color: "#9B83E8" }}>DATA MINIMIZATION</span>
              <h3 style={{ fontSize: 15, margin: "8px 0 10px" }}>Zero Sample Storage</h3>
              <p style={{ color: "#A1A8B8", fontSize: 11, lineHeight: 1.8 }}>
                The discovery engine profiles bounded rows in transient memory. Only schema metadata, rule matches, and evidence summaries are stored in the database—never raw personal records.
              </p>
            </div>

            <div className="panel" style={{ padding: 24, margin: 0 }}>
              <span className="eyebrow" style={{ color: "#9B83E8" }}>HUMAN REVIEW</span>
              <h3 style={{ fontSize: 15, margin: "8px 0 10px" }}>Review decisions stay explicit</h3>
              <p style={{ color: "#A1A8B8", fontSize: 11, lineHeight: 1.8 }}>
                Workspace data stays isolated by the browser key. Findings remain candidates until a person records a review decision and note.
              </p>
            </div>
          </div>
        </section>

        {/* Callout Section */}
        <section className="callout-section">
          <div className="page-width callout-inner">
            <div>
              <span className="eyebrow">ENTERPRISE PRIVACY WORKBENCH</span>
              <h2>Evidence you can trace.<br /><em>Decisions you can defend.</em></h2>
              <p>Privexis helps privacy engineers, data stewards, and auditors build a verifiable inventory without pretending that a scanner can decide legal context.</p>
            </div>
            <div style={{ display: "flex", gap: 12 }}>
              <Link href="/data-sources" className="button">
                Get started <ArrowRight size={16} />
              </Link>
              <Link href="/scanner" className="button button-outline">
                Start a scan <ArrowRight size={16} />
              </Link>
            </div>
          </div>
        </section>
      </main>
      <PublicFooter />
    </>
  );
}
