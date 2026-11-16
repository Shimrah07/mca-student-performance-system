/**
 * frontend/src/api/mcaApi.js
 *
 * MCA-specific API service module.
 * All calls to MCA backend endpoints are centralised here.
 *
 * Base URL is read from VITE_API_URL (defaults to http://localhost:8000).
 */

function getApiBaseUrl() {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  if (typeof window !== "undefined" && window.location.hostname === "127.0.0.1") {
    return "http://127.0.0.1:8000";
  }
  return "http://localhost:8000";
}

export const MCA_API_BASE_URL = getApiBaseUrl();

/** Reusable fetch wrapper with friendly error handling */
async function mcaFetch(endpoint, options = {}) {
  const url = `${MCA_API_BASE_URL}${endpoint}`;
  let response;
  try {
    response = await fetch(url, {
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      ...options,
    });
  } catch (err) {
    const error = new Error(
      `Cannot reach MCA backend at ${MCA_API_BASE_URL}. ` +
        "Make sure the FastAPI server is running (uvicorn app.main:app --reload)."
    );
    error.isNetworkError = true;
    error.originalError = err;
    throw error;
  }

  const contentType = response.headers.get("content-type");
  const isJson = contentType && contentType.includes("application/json");
  const data = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    let msg = `Request failed: ${response.status}`;
    if (isJson && data?.detail) {
      if (Array.isArray(data.detail)) {
        msg = data.detail.map((e) => `${e.loc?.join(" → ") ?? "field"}: ${e.msg}`).join(" | ");
      } else {
        msg = String(data.detail);
      }
    } else if (typeof data === "string" && data.trim()) {
      msg = data;
    }
    const error = new Error(msg);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

// ─── Health ────────────────────────────────────────────────────────────────

/** GET /health */
export async function getHealth() {
  return mcaFetch("/health", { method: "GET" });
}

/** GET /health/db */
export async function getDbHealth() {
  return mcaFetch("/health/db", { method: "GET" });
}

// ─── Curriculum ────────────────────────────────────────────────────────────

/** GET /api/mca/curriculum — Full 4-semester curriculum */
export async function getCurriculum() {
  return mcaFetch("/api/mca/curriculum", { method: "GET" });
}

/** GET /api/mca/semesters/:n — Single semester courses */
export async function getSemester(semesterNumber) {
  return mcaFetch(`/api/mca/semesters/${encodeURIComponent(semesterNumber)}`, { method: "GET" });
}

// ─── Predictions ───────────────────────────────────────────────────────────

/**
 * POST /api/mca/predictions/subject
 *
 * @param {{ registration_id: number, cutoff_timestamp: string, student_id?: number }} payload
 */
export async function predictSubject(payload) {
  return mcaFetch("/api/mca/predictions/subject", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/**
 * POST /api/mca/predictions/semester
 *
 * @param {{ student_id: number, target_semester: number, cutoff_timestamp: string }} payload
 */
export async function predictSemester(payload) {
  return mcaFetch("/api/mca/predictions/semester", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** GET /api/mca/predictions/:id */
export async function getPredictionById(predictionId) {
  return mcaFetch(`/api/mca/predictions/${encodeURIComponent(predictionId)}`, { method: "GET" });
}

/** GET /api/mca/predictions/student/:studentId?limit=N */
export async function getStudentPredictions(studentId, limit = 20) {
  return mcaFetch(
    `/api/mca/predictions/student/${encodeURIComponent(studentId)}?limit=${limit}`,
    { method: "GET" }
  );
}
