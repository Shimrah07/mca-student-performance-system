/**
 * frontend/src/components/Navbar.jsx
 *
 * Top navigation bar — premium Phase 4.8 styling.
 * Logic: health polling every 30s. Layout: brand + tab links + status pill.
 */

import { useEffect, useState } from "react";
import { getHealth, getDbHealth } from "../api/mcaApi";

const NAV_ITEMS = [
  { key: "overview",    label: "Overview",            icon: "◈" },
  { key: "curriculum",  label: "Curriculum",          icon: "⊟" },
  { key: "subject",     label: "Subject Assessment",  icon: "◎" },
  { key: "semester",    label: "Semester Assessment",  icon: "▦" },
  { key: "history",     label: "History",             icon: "⊡" },
  { key: "about",       label: "About",               icon: "ⓘ" },
];

export default function Navbar({ activeTab, setActiveTab }) {
  const [apiStatus, setApiStatus] = useState({ online: false, checking: true });
  const [dbStatus,  setDbStatus]  = useState({ connected: false, message: "" });

  useEffect(() => {
    let isMounted = true;

    async function probeSystem() {
      try {
        const health = await getHealth();
        if (isMounted) setApiStatus({ online: health?.status === "ok", checking: false });
      } catch {
        if (isMounted) setApiStatus({ online: false, checking: false });
      }

      try {
        const db = await getDbHealth();
        if (isMounted) setDbStatus({ connected: Boolean(db?.database_connected), message: db?.message || "" });
      } catch {
        if (isMounted) setDbStatus({ connected: false, message: "Database offline" });
      }
    }

    probeSystem();
    const interval = setInterval(probeSystem, 30000);
    return () => { isMounted = false; clearInterval(interval); };
  }, []);

  const statusDot = apiStatus.checking ? "amber" : apiStatus.online ? "green" : "red";
  const statusLabel = apiStatus.checking
    ? "Checking…"
    : apiStatus.online
      ? dbStatus.connected ? "API + MySQL Online" : "API Online · DB Offline"
      : "API Offline";

  const statusTitle = apiStatus.online
    ? `FastAPI Online | ${dbStatus.connected ? "MySQL Connected" : "Database Offline"}`
    : "FastAPI Offline (Check localhost:8000)";

  return (
    <header className="navbar">
      <div className="navbar-inner">

        {/* Brand */}
        <div className="brand-wrapper" onClick={() => setActiveTab("overview")}>
          <div className="brand-icon">🎓</div>
          <div>
            <div className="brand-title">MCA Performance System</div>
            <div className="brand-subtitle">
              Dept. of Computer Applications · UIT-RGPV (Autonomous)
            </div>
          </div>
        </div>

        {/* Navigation + Status */}
        <nav className="nav-links">
          {NAV_ITEMS.map(({ key, label }) => (
            <button
              key={key}
              type="button"
              className={`nav-btn${activeTab === key ? " active" : ""}`}
              onClick={() => setActiveTab(key)}
            >
              {label}
            </button>
          ))}

          <div className="system-status-pill" title={statusTitle}>
            <span className={`status-dot ${statusDot}`} />
            <span>{statusLabel}</span>
          </div>
        </nav>

      </div>
    </header>
  );
}
