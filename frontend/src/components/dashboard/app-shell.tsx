"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";

import { clearSession } from "../../services/auth";

type AppShellProps = {
  children: ReactNode;
};

function NavItem({ href, label, icon, active }: { href: string; label: string; icon: ReactNode; active: boolean }) {
  return (
    <a href={href} className={`cd-nav-item${active ? " is-active" : ""}`}>
      <span className="cd-nav-icon" aria-hidden="true">
        {icon}
      </span>
      {label}
    </a>
  );
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const dashboardActive = pathname === "/dashboard" || pathname.startsWith("/dashboard/bots");
  const analyticsActive = pathname.startsWith("/dashboard/analytics");

  function onLogout() {
    clearSession();
    window.location.replace("/login");
  }

  return (
    <div className="cd-app-root">
      <header className="cd-topbar">
        <a href="/dashboard" className="cd-brand">
          <span className="cd-brand-badge" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4 stroke-current">
              <rect x="3.5" y="7" width="17" height="12.5" rx="2.5" strokeWidth="1.7" />
              <path d="M8 7V5.6A1.6 1.6 0 019.6 4h4.8A1.6 1.6 0 0116 5.6V7M9 12h6M12 9v6" strokeWidth="1.7" />
            </svg>
          </span>
          <span className="cd-brand-text">ChatDock</span>
        </a>

        <nav className="cd-nav">
          <NavItem
            href="/dashboard"
            label="Dashboard"
            active={dashboardActive}
            icon={
              <svg viewBox="0 0 24 24" fill="none" className="h-3.5 w-3.5 stroke-current">
                <rect x="4" y="4" width="6.5" height="6.5" rx="1.4" strokeWidth="1.6" />
                <rect x="13.5" y="4" width="6.5" height="6.5" rx="1.4" strokeWidth="1.6" />
                <rect x="4" y="13.5" width="6.5" height="6.5" rx="1.4" strokeWidth="1.6" />
                <rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.4" strokeWidth="1.6" />
              </svg>
            }
          />
          <NavItem
            href="/dashboard/analytics"
            label="Analytics"
            active={analyticsActive}
            icon={
              <svg viewBox="0 0 24 24" fill="none" className="h-3.5 w-3.5 stroke-current">
                <path d="M5 18V9M11.5 18V5M18 18v-7M4 18h16" strokeWidth="1.7" />
              </svg>
            }
          />
        </nav>

        <button type="button" className="cd-logout-btn" onClick={onLogout}>
          <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4 stroke-current">
            <path d="M14 7l5 5-5 5M19 12H9M11 4H7a2 2 0 00-2 2v12a2 2 0 002 2h4" strokeWidth="1.6" />
          </svg>
          Logout
        </button>
      </header>

      <main className="cd-main">{children}</main>
    </div>
  );
}
