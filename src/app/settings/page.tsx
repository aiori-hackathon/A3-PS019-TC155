"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Database, HardDrive, ShieldCheck } from "lucide-react";
import { WorkspaceShell } from "@/components/workspace-shell";
import { api } from "@/lib/api";

type Rules = { version: string; classes: Record<string, string> };

export default function SettingsPage() {
  const [healthy, setHealthy] = useState<boolean | null>(null);
  const [rules, setRules] = useState<Rules | null>(null);
  useEffect(() => {
    api("/health/ready").then(() => setHealthy(true)).catch(() => setHealthy(false));
    api<Rules>("/rules").then(setRules).catch(() => setRules(null));
  }, []);

  return (
    <WorkspaceShell title="Workspace Settings">
      <div className="content-heading"><div><span className="eyebrow">LOCAL WORKSPACE</span><h2>Your scan environment</h2><p>No account is required. This browser has its own workspace key; its sources, findings, and review notes stay separated from other browsers.</p></div></div>
      <div className="settings-grid">
        <article className="panel settings-card"><span className="eyebrow">API STATUS</span><h3>{healthy === null ? "Checking…" : healthy ? "Connected" : "Offline"}</h3><p>The scanner API stores source files under the configured private uploads folder and limits row sampling.</p><div className="settings-field"><span>Database</span><b style={{ color: healthy ? "#63B79B" : "#D87980" }}>{healthy ? <><CheckCircle2 size={13} /> Ready</> : "Unavailable"}</b></div><div className="settings-field"><span>Maximum upload</span><b>15 MB</b></div><div className="settings-field"><span>Default scan sample</span><b>500 rows per table</b></div></article>
        <article className="panel settings-card"><span className="eyebrow">PRIVACY &amp; STORAGE</span><h3>Browser-local workspace</h3><p>A random workspace key in this browser isolates your sources from other visitors. Clearing site storage removes access to this workspace.</p><div className="settings-field"><span>Sample handling</span><b><ShieldCheck size={13} /> Bounded, no raw values in findings</b></div><div className="settings-field"><span>SQLite scanning</span><b><Database size={13} /> Read-only</b></div><div className="settings-field"><span>Uploads</span><b><HardDrive size={13} /> Local server storage</b></div></article>
        <article className="panel settings-card" style={{ gridColumn: "1/-1" }}><span className="eyebrow">CLASSIFIER</span><h3>Five configured personal-data classes</h3><div className="class-list">{Object.entries(rules?.classes || { C1: "Personal identity", C2: "Contact information", C3: "Government identifiers", C4: "Financial information", C5: "Location / address" }).map(([code, name]) => <div className="settings-field" key={code}><span>{code}</span><b>{name}</b></div>)}</div><p className="panel-note">Rule set {rules?.version || "loading"}. Anything that matches none is labelled not personal data.</p></article>
      </div>
    </WorkspaceShell>
  );
}
