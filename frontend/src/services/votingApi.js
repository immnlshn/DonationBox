/**
 * API Client für Voting Management Endpunkte
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

async function fetchJson(path, options = {}) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Accept": "application/json",
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    const err = new Error(`${options.method || "GET"} ${path} failed (${res.status}): ${text}`);
    err.status = res.status;
    throw err;
  }

  // DELETE returns 204 No Content
  if (res.status === 204) {
    return null;
  }

  return res.json();
}

/**
 * Holt alle Votings (mit Pagination)
 */
export async function getAllVotes(limit = 100, offset = 0) {
  return fetchJson(`/voting/?limit=${limit}&offset=${offset}`);
}

/**
 * Holt ein einzelnes Voting
 */
export async function getVoteById(voteId) {
  return fetchJson(`/voting/${voteId}`);
}

/**
 * Erstellt ein neues Voting
 * @param {Object} data - { question, start_time, end_time, categories: [{name}] }
 */
export async function createVote(data) {
  return fetchJson("/voting/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Aktualisiert ein Voting
 * @param {number} voteId
 * @param {Object} data - { question?, start_time?, end_time?, categories? }
 */
export async function updateVote(voteId, data) {
  return fetchJson(`/voting/${voteId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

/**
 * Löscht ein Voting
 * @param {number} voteId
 */
export async function deleteVote(voteId) {
  return fetchJson(`/voting/${voteId}`, {
    method: "DELETE",
  });
}

/**
 * Holt Totals für ein bestimmtes Voting
 */
export async function getVoteTotals(voteId) {
  return fetchJson(`/voting/${voteId}/totals`);
}

/**
 * Holt das aktive Voting
 */
export async function getActiveVote() {
  return fetchJson("/voting/active");
}

/**
 * Holt Totals für das aktive Voting
 */
export async function getActiveVoteTotals() {
  return fetchJson("/voting/active/totals");
}
