/**
 * frontend/src/components/TopBar.jsx
 *
 * Slim top utility bar inspired by the reference design.
 * Features mobile drawer toggle, minimal search pill, and session pill.
 */

import { MenuIcon, SearchIcon } from "./common/Icons";

export default function TopBar({ onOpenSidebar, activeTab, onNavigate }) {
  const getTabLabel = (tab) => {
    switch (tab) {
      case "overview": return "Dashboard & Performance Metrics";
      case "curriculum": return "Official Autonomous Curriculum";
      case "subject": return "Subject-Level Prediction Engine";
      case "semester": return "Semester-Level Prediction Engine";
      case "history": return "Student Prediction Audit Trail";
      case "about": return "Project Methodology & Ethics";
      default: return "Academic Support System";
    }
  };

  const handleSearchKeyDown = (e) => {
    if (e.key === "Enter") {
      const val = e.target.value.trim().toLowerCase();
      if (val.includes("curr") || val.includes("course") || val.includes("mca")) {
        onNavigate("curriculum");
      } else if (val.includes("subj") || val.includes("108") || val.includes("109")) {
        onNavigate("subject");
      } else if (val.includes("sem")) {
        onNavigate("semester");
      } else if (val.includes("hist") || val.includes("demo") || val.match(/^\d+$/)) {
        onNavigate("history");
      } else if (val.includes("about") || val.includes("model")) {
        onNavigate("about");
      }
    }
  };

  return (
    <header className="topbar">
      <div className="topbar-left">
        {/* Mobile menu trigger */}
        <button
          type="button"
          className="topbar-menu-btn"
          onClick={onOpenSidebar}
          aria-label="Open Navigation Menu"
        >
          <MenuIcon size={20} />
        </button>

        {/* Breadcrumb / Title indicator */}
        <div className="topbar-title-wrap">
          <span className="topbar-section-title">{getTabLabel(activeTab)}</span>
        </div>
      </div>

      <div className="topbar-right">
        {/* Minimal Search Pill from Reference Image */}
        <div className="topbar-search-pill">
          <SearchIcon size={15} className="topbar-search-icon" />
          <input
            type="text"
            className="topbar-search-input"
            placeholder="Search course code, student ID, or semester..."
            onKeyDown={handleSearchKeyDown}
            aria-label="Quick search navigation"
          />
          <kbd className="topbar-search-kbd">/</kbd>
        </div>

        {/* Academic Session Pill */}
        <div className="topbar-session-badge">
          <span className="session-dot" />
          <span>Session 2026–27</span>
        </div>
      </div>
    </header>
  );
}
