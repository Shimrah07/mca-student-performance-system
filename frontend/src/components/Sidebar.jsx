/**
 * frontend/src/components/Sidebar.jsx
 *
 * Minimal persistent left sidebar navigation inspired by the SaaS reference design.
 * Clean typography, elegant line icons, subtle forest-green active highlight,
 * and mobile drawer responsiveness.
 */

import { useEffect, useState } from "react";
import { getHealth, getDbHealth } from "../api/mcaApi";
import {
  DashboardIcon,
  CurriculumIcon,
  SubjectIcon,
  SemesterIcon,
  HistoryIcon,
  AboutIcon,
  CloseIcon,
  AcademicCapIcon,
} from "./common/Icons";

const NAV_MENU = [
  { id: "overview", label: "Dashboard", desc: "Overview & metrics", icon: DashboardIcon },
  { id: "curriculum", label: "Curriculum", desc: "4 Semesters · 26 courses", icon: CurriculumIcon },
  { id: "subject", label: "Subject Assessment", desc: "Single course tier prediction", icon: SubjectIcon },
  { id: "semester", label: "Semester Assessment", desc: "Aggregate semester tier", icon: SemesterIcon },
  { id: "history", label: "Prediction History", desc: "Immutable audit records", icon: HistoryIcon },
];

const NAV_GENERAL = [
  { id: "about", label: "About & Methodology", desc: "Ethics & ML architecture", icon: AboutIcon },
];

export default function Sidebar({ activeTab, setActiveTab, isOpen, onClose }) {
  const [apiStatus, setApiStatus] = useState({ online: false, checking: true });
  const [dbStatus, setDbStatus] = useState({ connected: false, message: "" });

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
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleNavClick = (id) => {
    setActiveTab(id);
    if (onClose) onClose();
  };

  const statusDotClass = apiStatus.checking ? "amber" : apiStatus.online ? "green" : "red";
  const statusText = apiStatus.checking
    ? "Checking API..."
    : apiStatus.online
    ? dbStatus.connected
      ? "API + MySQL Online"
      : "API Online (DB Offline)"
    : "System Offline";

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && <div className="sidebar-backdrop" onClick={onClose} aria-hidden="true" />}

      {/* Persistent Left Sidebar */}
      <aside className={`sidebar ${isOpen ? "sidebar-open" : ""}`} aria-label="Main Navigation">
        {/* Brand Header */}
        <div className="sidebar-brand-wrapper">
          <div className="sidebar-brand-icon">
            <AcademicCapIcon size={22} />
          </div>
          <div className="sidebar-brand-text">
            <span className="sidebar-brand-title">MCA Intelligence</span>
            <span className="sidebar-brand-dept">UIT-RGPV (Autonomous)</span>
          </div>

          {/* Close button for mobile drawer */}
          <button
            type="button"
            className="sidebar-close-btn"
            onClick={onClose}
            aria-label="Close Navigation"
          >
            <CloseIcon size={18} />
          </button>
        </div>

        {/* Navigation Groups */}
        <div className="sidebar-nav-container">
          {/* Main Menu */}
          <div className="sidebar-group">
            <div className="sidebar-group-title">ACADEMIC MENU</div>
            <nav className="sidebar-nav-list">
              {NAV_MENU.map((item) => {
                const IconComponent = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    className={`sidebar-nav-item ${isActive ? "active" : ""}`}
                    onClick={() => handleNavClick(item.id)}
                  >
                    <span className="sidebar-item-icon">
                      <IconComponent size={18} />
                    </span>
                    <span className="sidebar-item-label">{item.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* General / System */}
          <div className="sidebar-group">
            <div className="sidebar-group-title">SYSTEM</div>
            <nav className="sidebar-nav-list">
              {NAV_GENERAL.map((item) => {
                const IconComponent = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    type="button"
                    className={`sidebar-nav-item ${isActive ? "active" : ""}`}
                    onClick={() => handleNavClick(item.id)}
                  >
                    <span className="sidebar-item-icon">
                      <IconComponent size={18} />
                    </span>
                    <span className="sidebar-item-label">{item.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Sidebar Footer: System Status */}
        <div className="sidebar-footer">
          <div className="sidebar-status-card">
            <div className="sidebar-status-row">
              <span className={`status-indicator-dot ${statusDotClass}`} />
              <span className="sidebar-status-title">{statusText}</span>
            </div>
            <div className="sidebar-status-caption">
              Autonomous Session 2026–27
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
