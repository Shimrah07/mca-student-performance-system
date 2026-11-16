/**
 * frontend/src/components/PredictionHistory.jsx
 *
 * Displays previously persisted prediction records with pagination and detailed modal inspection.
 */

import { useEffect, useState } from "react";
import { getPredictionHistory, getPredictionById } from "../api/client";
import RecordDetailModal from "./RecordDetailModal";

function getCategoryBadgeClass(category) {
  switch (category) {
    case "Excellent":
      return "badge excellent";
    case "Good":
      return "badge good";
    case "Average":
      return "badge average";
    case "Needs Improvement":
    default:
      return "badge needs-improvement";
  }
}

export default function PredictionHistory({ onNavigateToForm }) {
  const [historyData, setHistoryData] = useState({ total: 0, items: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [page, setPage] = useState(0);
  const limit = 10;

  const [selectedRecord, setSelectedRecord] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const fetchHistory = async (pageNum = 0) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getPredictionHistory(limit, pageNum * limit);
      setHistoryData(data);
    } catch {
      setError(
        "Could not load prediction history. The local database service might be offline, or no records have been saved yet."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let ignore = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await getPredictionHistory(limit, page * limit);
        if (!ignore) {
          setHistoryData(data);
        }
      } catch {
        if (!ignore) {
          setError(
            "Could not load prediction history. The local database service might be offline, or no records have been saved yet."
          );
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      ignore = true;
    };
  }, [page]);

  const handleOpenDetail = async (id) => {
    setLoadingDetail(true);
    try {
      const detail = await getPredictionById(id);
      setSelectedRecord(detail);
    } catch (err) {
      alert(`Failed to load record #${id}: ${err.message}`);
    } finally {
      setLoadingDetail(false);
    }
  };

  const totalPages = Math.ceil(historyData.total / limit) || 1;

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h2 className="card-title">Prediction & Support History</h2>
          <p className="card-subtitle">
            Audit trail of saved performance assessments and guidance payloads.
          </p>
        </div>

        <button
          type="button"
          className="btn-sample"
          style={{ padding: "8px 14px" }}
          onClick={() => fetchHistory(page)}
          disabled={loading}
        >
          {loading ? "Refreshing..." : "🔄 Refresh History"}
        </button>
      </div>

      {error && (
        <div className="alert-box alert-warning">
          <strong>Database Notice:</strong> {error}
        </div>
      )}

      {loading && !historyData.items.length ? (
        <div className="empty-state">
          <div className="spinner" style={{ borderColor: "rgba(37, 99, 235, 0.3)", borderTopColor: "var(--color-primary)" }} />
          <p style={{ marginTop: "12px" }}>Loading prediction history from database...</p>
        </div>
      ) : historyData.items.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📂</div>
          <h3 style={{ fontSize: "16px", fontWeight: 700, marginBottom: "6px" }}>
            No Saved Predictions Found
          </h3>
          <p style={{ fontSize: "13px", maxWidth: "480px", margin: "0 auto 16px" }}>
            Predictions conducted with database persistence enabled will be cataloged here for
            longitudinal student progress tracking.
          </p>
          <button
            type="button"
            className="btn-primary"
            style={{ fontSize: "13px", padding: "8px 16px" }}
            onClick={onNavigateToForm}
          >
            Start First Assessment
          </button>
        </div>
      ) : (
        <>
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Student Link</th>
                  <th>Subject</th>
                  <th>Scenario</th>
                  <th>Predicted Category</th>
                  <th>Classifier Model</th>
                  <th>Assessment Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {historyData.items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <strong>#{item.id}</strong>
                    </td>
                    <td>
                      {item.student_id ? (
                        <span className="badge" style={{ backgroundColor: "#e0e7ff", color: "#3730a3" }}>
                          Student #{item.student_id}
                        </span>
                      ) : (
                        <span className="badge badge-guest">Guest</span>
                      )}
                    </td>
                    <td>{item.subject}</td>
                    <td>
                      <span style={{ fontSize: "12px", color: "var(--color-slate)" }}>
                        {item.scenario}
                      </span>
                    </td>
                    <td>
                      <span className={getCategoryBadgeClass(item.predicted_category)}>
                        {item.predicted_category}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: "11px", color: "var(--color-muted)" }}>
                        {item.model_name}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: "12px" }}>
                        {item.created_at
                          ? new Date(item.created_at).toLocaleDateString() + " " +
                            new Date(item.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                          : "—"}
                      </span>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn-view-record"
                        onClick={() => handleOpenDetail(item.id)}
                        disabled={loadingDetail}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination bar */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "18px", fontSize: "13px", color: "var(--color-muted)" }}>
            <div>
              Showing {historyData.items.length} of {historyData.total} records (Page {page + 1} of {totalPages})
            </div>

            <div style={{ display: "flex", gap: "8px" }}>
              <button
                type="button"
                className="btn-sample"
                disabled={page <= 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
              >
                ◀ Previous
              </button>
              <button
                type="button"
                className="btn-sample"
                disabled={page + 1 >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next ▶
              </button>
            </div>
          </div>
        </>
      )}

      {selectedRecord && (
        <RecordDetailModal
          record={selectedRecord}
          onClose={() => setSelectedRecord(null)}
        />
      )}
    </div>
  );
}
