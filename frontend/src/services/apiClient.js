/**
 * Minimal REST client for the backend API (OpenAPI).
 *
 * Used to hydrate the UI on page load so the screen is not empty after reload:
 * - GET /voting/active
 * - GET /voting/active/totals
 *
 * If there is no active vote, backend returns 404 (expected during setup).
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

async function getJson(path) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "GET",
    headers: { Accept: "application/json" },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    const err = new Error(`GET ${path} failed (${res.status}): ${text}`);
    err.status = res.status;
    throw err;
  }

  return res.json();
}

export async function getActiveVote() {
  // OpenAPI: GET /voting/active
  return getJson("/voting/active");
}

export async function getActiveVoteTotals() {
  // OpenAPI: GET /voting/active/totals
  return getJson("/voting/active/totals");
}