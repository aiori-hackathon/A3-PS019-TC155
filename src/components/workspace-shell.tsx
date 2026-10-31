"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  AlertTriangle,
  Boxes,
  ClipboardCheck,
  FileBarChart,
  FileText,
  History,
  LayoutDashboard,
  MessageSquareText,
  ScanSearch,
  Settings2,
  ShieldAlert,
  ShieldCheck,
  Sliders,
} from "lucide-react";
import { useEffect, useState } from "react";
import { api, User } from "@/lib/api";
import { Brand } from "./brand";

const navItems = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Data Sources", href: "/data-sources", icon: Boxes },
  { label: "Discovery Scanner", href: "/scanner", icon: ScanSearch },
  { label: "Personal Data Inventory", href: "/inventory", icon: ClipboardCheck },
  { label: "Metadata Management", href: "/metadata", icon: FileText },
  { label: "Evidence Review Center", href: "/review", icon: ShieldCheck },
  { label: "Detection Rules", href: "/rules", icon: Sliders },
  { label: "Evaluation Center", href: "/evaluation", icon: Activity },
  { label: "Evidence Gap Analysis", href: "/evidence-gaps", icon: AlertTriangle },
  { label: "Reports Center", href: "/reports", icon: FileBarChart },
  { label: "Scan History", href: "/scan-history", icon: History },
  { label: "Privexis Assistant", href: "/assistant", icon: MessageSquareText },
  { label: "Settings", href: "/settings", icon: Settings2 },
];

export function WorkspaceShell({ children, title }: { children: React.ReactNode; title: string }) {
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    api<User>("/auth/me")
      .then((data) => {
        if (active) setUser(data);
      })
      .catch(() => {
        if (active) setError("Your local workspace could not be reached. Check that the API is running and refresh this page.");
      });
    return () => {
      active = false;
    };
  }, []);

  const displayName = user?.full_name || "Local workspace";
  const avatarLetter = "P";

  return (
    <div className="workspace-shell">
      <aside className="workspace-sidebar">
        <Brand />
        <div className="workspace-label">ENTERPRISE CONSOLE</div>
        <nav aria-label="Workspace navigation" style={{ overflowY: "auto", flex: 1, paddingRight: 4 }}>
          {navItems.map(({ label, href, icon: Icon }) => {
            const isActive = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
            return (
              <Link
                key={href}
                href={href}
                className={isActive ? "side-link side-active" : "side-link"}
              >
                <Icon size={16} strokeWidth={1.7} />
                <span>{label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-bottom">
          <div className="profile">
            <div className="avatar">{avatarLetter}</div>
            <div className="profile-copy"><strong>{displayName}</strong><small>Stored in this browser</small></div>
          </div>
          <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "center", padding: "4px 8px" }}>
            <Link href="/settings" className="side-link" style={{ padding: "0 6px", fontSize: 10 }}>
              <Settings2 size={14} />
              <span>Settings</span>
            </Link>
          </div>
        </div>
      </aside>

      <main className="workspace-main">
        <header className="workspace-top">
          <div className="mobile-brand">
            <Brand />
          </div>
          <div>
            <span className="eyebrow">PRIVACY EVIDENCE WORKBENCH &bull; PS-019</span>
            <h1>{title}</h1>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div className="top-status">
              <span className="status-dot" /> Local Processing Active
            </div>
            <span className="quiet-link">Browser-local workspace</span>
          </div>
        </header>

        <div className="workspace-content">
          {error && <div className="notice notice-error" role="alert">{error}</div>}
          {children}
        </div>
      </main>
    </div>
  );
}
