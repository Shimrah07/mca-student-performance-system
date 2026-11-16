/**
 * frontend/src/App.jsx
 *
 * Master Application Shell with persistent left sidebar navigation
 * and spacious main content area.
 * Inspired by minimal, high-end academic SaaS product design.
 */

import { useState } from "react";
import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";
import McaOverview from "./components/mca/McaOverview";
import McaCurriculumBrowser from "./components/mca/McaCurriculumBrowser";
import McaSubjectPredictionForm from "./components/mca/McaSubjectPredictionForm";
import McaSemesterPredictionForm from "./components/mca/McaSemesterPredictionForm";
import McaPredictionHistoryPanel from "./components/mca/McaPredictionHistoryPanel";
import AboutModal from "./components/AboutModal";
import "./App.css";

export default function App() {
  const [activeTab, setActiveTab] = useState("overview");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="app-shell">
      {/* Persistent Left Sidebar with Mobile Drawer support */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main Content Area */}
      <div className="main-wrapper">
        <TopBar
          activeTab={activeTab}
          onNavigate={(tab) => setActiveTab(tab)}
          onOpenSidebar={() => setSidebarOpen(true)}
        />

        <main className="main-content">
          {activeTab === "overview" && (
            <McaOverview onNavigate={(tab) => setActiveTab(tab)} />
          )}
          {activeTab === "curriculum" && <McaCurriculumBrowser />}
          {activeTab === "subject" && <McaSubjectPredictionForm />}
          {activeTab === "semester" && <McaSemesterPredictionForm />}
          {activeTab === "history" && <McaPredictionHistoryPanel />}
          {activeTab === "about" && <AboutModal />}
        </main>

        <footer className="academic-footer">
          <div className="footer-title">
            <strong>AI-Based Student Performance Prediction &amp; Academic Support System</strong>
            <span className="footer-badge">MCA 3rd Sem Minor Project</span>
          </div>
          <div className="footer-subtext">
            Department of Computer Applications · UIT-RGPV (Autonomous), Bhopal · Academic Session 2026–27
          </div>
        </footer>
      </div>
    </div>
  );
}
