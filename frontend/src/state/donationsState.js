/**
 * donationsState.js
 *
 * Responsibilities:
 *  - Hold minimal UI state for totals, recent donations, and chart results
 *  - Hydrate state from REST (OpenAPI)
 *  - Update state from WebSocket donation broadcasts
 *
 * REST (OpenAPI):
 *  - GET /voting/active -> VoteResponse (question + categories)  :contentReference[oaicite:2]{index=2}
 *  - GET /voting/active/totals -> DonationTotalsResponse         :contentReference[oaicite:3]{index=3}
 *
 * WebSocket:
 *  - type: "donation_created"
 *  - data.totals contains total_amount_cents, total_donations, category_totals
 *
 * Fallback behavior:
 *  - If there is no active vote, we still show a neutral question and two generic categories.
 *  - The chart always receives results entries (0%) so the UI does not look "empty".
 */

const FALLBACK_QUESTION = "Aktuelle Abstimmung";
const FALLBACK_CATEGORIES = [
  { id: 0, name: "Option 1" },
  { id: 1, name: "Option 2" },
];

export const initialState = {
  connection: "disconnected",

  questionText: FALLBACK_QUESTION,
  categories: FALLBACK_CATEGORIES, // [{id, name}]

  totalAmountCents: 0,
  totalDonationsCount: 0,
  categoryTotalsById: {}, // keys are strings, e.g. {"3": 200, "4": 500}

  recentDonationsCents: [], // last 3 amounts from WS events only
  results: buildResults(FALLBACK_CATEGORIES, {}), // ensure chart skeleton is rendered
};

export function centsToEuroString(cents) {
  const euros = (cents / 100).toFixed(2).replace(".", ",");
  return `${euros} €`;
}

function clampRecent(list, max = 3) {
  return list.slice(0, max);
}

/**
 * Builds chart entries from categories + category_totals.
 * Always returns one bar per category.
 */
export function buildResults(categories, categoryTotalsById) {
  const cats = Array.isArray(categories) && categories.length > 0 ? categories : FALLBACK_CATEGORIES;

  const entries = cats.map((c) => {
    const key = String(c.id); // JSON object keys are strings
    const cents = Number(categoryTotalsById?.[key] ?? 0);
    return { name: c.name, cents: Number.isFinite(cents) ? cents : 0 };
  });

  const total = entries.reduce((sum, e) => sum + e.cents, 0);

  if (total <= 0) {
    return entries.map((e) => ({ name: e.name, percent: 0 }));
  }

  return entries.map((e) => ({
    name: e.name,
    percent: Math.round((e.cents / total) * 1000) / 10, // 1 decimal place
  }));
}

/**
 * Apply VoteResponse from GET /voting/active.
 * VoteResponse contains: question, categories[{id,name}], ... :contentReference[oaicite:4]{index=4}
 */
export function applyActiveVote(state, voteResponse) {
  const question = (voteResponse?.question ?? "").trim();
  const categories = Array.isArray(voteResponse?.categories) ? voteResponse.categories : [];

  const nextQuestion = question.length > 0 ? question : FALLBACK_QUESTION;
  const nextCategories = categories.length > 0 ? categories : FALLBACK_CATEGORIES;

  const next = {
    ...state,
    questionText: nextQuestion,
    categories: nextCategories,
  };

  return {
    ...next,
    results: buildResults(next.categories, next.categoryTotalsById),
  };
}

/**
 * Apply DonationTotalsResponse from GET /voting/active/totals.
 * Schema: { vote_id, total_amount_cents, total_donations, category_totals } :contentReference[oaicite:5]{index=5}
 */
export function applyActiveTotals(state, totalsResponse) {
  const totalAmountCents = Number(totalsResponse?.total_amount_cents);
  const totalDonationsCount = Number(totalsResponse?.total_donations);

  const categoryTotalsById =
    totalsResponse?.category_totals && typeof totalsResponse.category_totals === "object"
      ? totalsResponse.category_totals
      : state.categoryTotalsById;

  const next = {
    ...state,
    totalAmountCents: Number.isFinite(totalAmountCents) ? totalAmountCents : state.totalAmountCents,
    totalDonationsCount: Number.isFinite(totalDonationsCount) ? totalDonationsCount : state.totalDonationsCount,
    categoryTotalsById,
  };

  return {
    ...next,
    results: buildResults(next.categories, next.categoryTotalsById),
  };
}

/**
 * Reduce WebSocket messages into state.
 * We only care about donation_created broadcasts.
 */
export function reduceWsMessage(state, msg) {
  if (!msg || typeof msg !== "object") return state;

  switch (msg.type) {
    case "donation_created": {
      const d = msg.data ?? {};
      const totals = d.totals ?? {};

      const totalAmountCents = Number(totals.total_amount_cents);
      const totalDonationsCount = Number(totals.total_donations);

      const categoryTotalsById =
        totals.category_totals && typeof totals.category_totals === "object"
          ? totals.category_totals
          : state.categoryTotalsById;

      const amountCents = Number(d.amount_cents);

      const next = {
        ...state,
        totalAmountCents: Number.isFinite(totalAmountCents) ? totalAmountCents : state.totalAmountCents,
        totalDonationsCount: Number.isFinite(totalDonationsCount) ? totalDonationsCount : state.totalDonationsCount,
        categoryTotalsById,
        recentDonationsCents:
          Number.isFinite(amountCents) && amountCents > 0
            ? clampRecent([amountCents, ...state.recentDonationsCents], 3)
            : state.recentDonationsCents,
      };

      return {
        ...next,
        results: buildResults(next.categories, next.categoryTotalsById),
      };
    }

    default:
      return state;
  }
}
