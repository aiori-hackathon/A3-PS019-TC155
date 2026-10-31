const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
let csrfToken = "";
let csrfWorkspaceKey = "";
let memoryWorkspaceKey = "";
const noCsrf = new Set<string>();

function getWorkspaceKey(): string {
  if (typeof window === "undefined") return "";
  try {
    const stored = localStorage.getItem("privexis_workspace_key");
    if (stored && /^[0-9a-f]{64}$/i.test(stored)) return stored;
    const bytes = new Uint8Array(32);
    window.crypto.getRandomValues(bytes);
    memoryWorkspaceKey = Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("");
    localStorage.setItem("privexis_workspace_key", memoryWorkspaceKey);
    localStorage.removeItem("privexis_token");
    return memoryWorkspaceKey;
  } catch {
    if (!memoryWorkspaceKey) {
      const bytes = new Uint8Array(32);
      window.crypto.getRandomValues(bytes);
      memoryWorkspaceKey = Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("");
    }
    return memoryWorkspaceKey;
  }
}

export function getStoredToken(): string {
  return "";
}

export function setStoredToken(token: string): void {
  void token;
  if (typeof window !== "undefined") { try { localStorage.removeItem("privexis_token"); } catch { /* Workspace storage may be disabled. */ } }
}

async function loadCsrf() {
  const workspaceKey = getWorkspaceKey();
  if (!workspaceKey || (csrfToken && csrfWorkspaceKey === workspaceKey) || typeof window === "undefined") return;
  try {
    const headers = new Headers();
    headers.set("X-Workspace-Key", workspaceKey);
    const response = await fetch(`${API}/api/v1/auth/me`, { headers, credentials: "include", cache: "no-store" });
    if (response.ok) {
      const data = await response.json();
      csrfToken = data.csrf_token || "";
      csrfWorkspaceKey = workspaceKey;
    }
  } catch {
    /* API unavailable fallback */
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const method = (options.method || "GET").toUpperCase();
  const headers = new Headers(options.headers);
  
  if (!(options.body instanceof FormData) && options.body) {
    headers.set("Content-Type", "application/json");
  }
  
  const workspaceKey = getWorkspaceKey();
  if (workspaceKey) headers.set("X-Workspace-Key", workspaceKey);
  if (csrfWorkspaceKey !== workspaceKey) csrfToken = "";
  
  if (!["GET", "HEAD", "OPTIONS"].includes(method) && !noCsrf.has(path)) {
    await loadCsrf();
    if (csrfToken) headers.set("X-CSRF-Token", csrfToken);
  }
  
  const response = await fetch(`${API}/api/v1${path}`, {
    ...options,
    method,
    headers,
    credentials: "include",
    cache: "no-store",
  });
  
  if (!response.ok) {
    if (response.status === 401 && typeof window !== "undefined") {
      setStoredToken("");
    }
    let message = `Request failed (${response.status})`;
    try {
      const errData = await response.json();
      message = errData.detail || errData.message || message;
    } catch {
      /* Keep safe fallback */
    }
    throw new Error(message);
  }
  
  const data = await response.json();
  if (data && typeof data.csrf_token === "string") {
    csrfToken = data.csrf_token;
  }
  if (data && typeof data.token === "string") {
    setStoredToken(data.token);
  }
  
  return data as T;
}

export async function download(path: string, filename: string) {
  const headers = new Headers();
  const workspaceKey = getWorkspaceKey();
  if (workspaceKey) headers.set("X-Workspace-Key", workspaceKey);
  
  const response = await fetch(`${API}/api/v1${path}`, {
    headers,
    credentials: "include",
    cache: "no-store",
  });
  
  if (!response.ok) throw new Error("Could not download this report.");
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export type User = {
  id: number;
  email: string;
  full_name: string;
  role: string;
  organization_id: number;
  mfa_enabled: boolean;
  csrf_token?: string;
};

export type Source = {
  id: number;
  name: string;
  kind: string;
  size_bytes: number;
  created_at: string;
};

export type Scan = {
  id: number;
  source_id: number;
  source_name: string;
  status: string;
  inspected_columns: number;
  rows_sampled: number;
  rule_version: string;
  enabled_classes?: string[];
  findings_count?: number;
  error_message?: string | null;
  created_at: string;
};

export type Finding = {
  id: number;
  scan_id: number;
  source_id: number;
  source: string;
  table_name: string;
  column_name: string;
  data_class: string;
  class_name: string;
  confidence: string;
  rule_id: string;
  evidence: string;
  review_status: string;
  review_note?: string;
  purpose: string;
  retention: string;
  created_at: string;
};

export type MetadataRecord = {
  id: number;
  source_id: number;
  source: string;
  table_name: string;
  column_name: string;
  purpose: string;
  retention: string;
};

export type RuleDefinition = {
  id: string;
  name: string;
  data_class: string;
  class_name: string;
  pattern: string;
  format_validator: string;
  confidence: string;
  enabled: boolean;
  version: string;
  description: string;
};

export type Metric = {
  class_code: string;
  class_name: string;
  tp: number;
  fp: number;
  fn: number;
  precision: number | null;
  recall: number | null;
  f1: number | null;
};

export type GapItem = {
  id: number;
  source_id: number;
  source_name: string;
  table_name: string;
  column_name: string;
  data_class: string;
  class_name: string;
  confidence: string;
  review_status: string;
  purpose: string;
  retention: string;
};

export type EvidenceGapsData = {
  completeness_score: number;
  total_findings: number;
  counts: {
    missing_purpose: number;
    missing_retention: number;
    pending_review: number;
  };
  missing_purpose: GapItem[];
  missing_retention: GapItem[];
  pending_review: GapItem[];
};
