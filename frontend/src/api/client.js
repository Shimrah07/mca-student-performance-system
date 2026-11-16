/**
 * frontend/src/api/client.js
 *
 * Dedicated HTTP API service for communicating with the FastAPI backend.
 * Uses configurable base URL via VITE_API_URL, dynamically aligning with
 * the browser's hostname (127.0.0.1 or localhost on port 8000).
 */

function getApiBaseUrl() {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  // Align API base URL with frontend hostname to prevent cross-hostname confusion
  if (typeof window !== "undefined" && window.location.hostname === "127.0.0.1") {
    return "http://127.0.0.1:8000";
  }
  return "http://localhost:8000";
}

export const API_BASE_URL = getApiBaseUrl();

/**
 * Helper to process HTTP responses and surface friendly error messages.
 */
async function handleResponse(response) {
  const contentType = response.headers.get("content-type");
  const isJson = contentType && contentType.includes("application/json");
  const data = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`;

    if (isJson && data && data.detail) {
      if (Array.isArray(data.detail)) {
        // FastAPI / Pydantic validation error array
        errorMessage = data.detail
          .map((err) => `${err.loc ? err.loc.join(" -> ") : "field"}: ${err.msg}`)
          .join(" | ");
      } else {
        errorMessage = String(data.detail);
      }
    } else if (typeof data === "string" && data.trim()) {
      errorMessage = data;
    }

    const error = new Error(errorMessage);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

/**
 * Robust wrapper around window.fetch with friendly network and CORS error messages.
 */
async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  let response;
  try {
    response = await fetch(url, options);
  } catch (err) {
    const currentOrigin =
      typeof window !== "undefined" ? window.location.origin : "http://127.0.0.1:5173";
    const networkError = new Error(
      `Unable to communicate with the backend at ${API_BASE_URL}. ` +
      `Please ensure the FastAPI server is running and that CORS allows origin '${currentOrigin}'.`
    );
    networkError.originalError = err;
    networkError.isNetworkError = true;
    throw networkError;
  }
  return handleResponse(response);
}

/**
 * Submit student data to the predictive model and retrieve supportive guidance.
 *
 * @param {Object} payload { subject, scenario, features, student_code? }
 * @returns {Promise<Object>} PredictionResponse
 */
export async function predictStudentPerformance(payload) {
  return apiFetch("/api/predictions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(payload),
  });
}

/**
 * Retrieve paginated list of previous predictions from database.
 *
 * @param {number} limit Maximum items to return
 * @param {number} offset Offset for pagination
 * @returns {Promise<Object>} PredictionListResponse
 */
export async function getPredictionHistory(limit = 10, offset = 0) {
  return apiFetch(`/api/predictions?limit=${encodeURIComponent(limit)}&offset=${encodeURIComponent(offset)}`, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
  });
}

/**
 * Retrieve an individual saved prediction record by ID.
 *
 * @param {number|string} predictionId
 * @returns {Promise<Object>} PredictionHistoryItem
 */
export async function getPredictionById(predictionId) {
  return apiFetch(`/api/predictions/${encodeURIComponent(predictionId)}`, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
  });
}

/**
 * Check backend system health.
 *
 * @returns {Promise<Object>} { status, message, environment }
 */
export async function checkHealth() {
  return apiFetch("/health", {
    method: "GET",
    headers: { Accept: "application/json" },
  });
}

/**
 * Check backend database connectivity status.
 *
 * @returns {Promise<Object>} { database_connected, message, database_url }
 */
export async function checkDbHealth() {
  return apiFetch("/health/db", {
    method: "GET",
    headers: { Accept: "application/json" },
  });
}
