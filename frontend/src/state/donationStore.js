/**
 * Unified Donation Store
 *
 * Single source of truth for all donation-related state:
 * - Connection status
 * - Vote data (question, categories)
 * - Totals & statistics
 * - Session state (popup flow)
 */

export const SESSION_STATES = {
  IDLE: "idle",
  CATEGORY_CHOSEN: "category_chosen",
  COLLECTING_MONEY: "collecting_money",
  DONATION_COMPLETE: "donation_complete",
};

const FALLBACK_QUESTION = "Aktuelle Abstimmung";
const FALLBACK_CATEGORIES = [
  { id: 0, name: "Option 1" },
  { id: 1, name: "Option 2" },
];

// ============================================================================
// INITIAL STATE
// ============================================================================

export const initialState = {
  // Connection
  connection: "disconnected",

  // Vote data
  questionText: FALLBACK_QUESTION,
  categories: FALLBACK_CATEGORIES,

  // Totals
  totalAmountCents: 0,
  totalDonationsCount: 0,
  categoryTotalsById: {},
  recentDonationsCents: [],
  results: buildResults(FALLBACK_CATEGORIES, {}),

  // Session state (for popup)
  sessionState: SESSION_STATES.IDLE,
  sessionCategoryId: null,
  sessionCategoryName: null,
  sessionCategoryChosenAt: null,
  sessionTotalMoney: 0,
  sessionLastMoneyAt: null,
  sessionDonationData: null,
  sessionDonationCompletedAt: null,
};

// ============================================================================
// HELPERS
// ============================================================================

export function centsToEuroString(cents) {
  const euros = (cents / 100).toFixed(2).replace(".", ",");
  return `${euros} €`;
}

function clampRecent(list, max = 3) {
  return list.slice(0, max);
}

function buildResults(categories, categoryTotalsById) {
  const cats = Array.isArray(categories) && categories.length > 0 ? categories : FALLBACK_CATEGORIES;

  const entries = cats.map((c) => {
    const key = String(c.id);
    const cents = Number(categoryTotalsById?.[key] ?? 0);
    return { name: c.name, cents: Number.isFinite(cents) ? cents : 0 };
  });

  const total = entries.reduce((sum, e) => sum + e.cents, 0);

  if (total <= 0) {
    return entries.map((e) => ({ name: e.name, percent: 0 }));
  }

  return entries.map((e) => ({
    name: e.name,
    percent: Math.round((e.cents / total) * 1000) / 10,
  }));
}

// ============================================================================
// REDUCER
// ============================================================================

export function reducer(state, action) {
  switch (action.type) {
    // -------------------------------------------------------------------------
    // CONNECTION
    // -------------------------------------------------------------------------
    case "connection":
      return { ...state, connection: action.status };

    // -------------------------------------------------------------------------
    // REST API HYDRATION
    // -------------------------------------------------------------------------
    case "active_vote": {
      const vote = action.vote;
      const question = (vote?.question ?? "").trim();
      const categories = Array.isArray(vote?.categories) ? vote.categories : [];

      const nextQuestion = question.length > 0 ? question : FALLBACK_QUESTION;
      const nextCategories = categories.length > 0 ? categories : FALLBACK_CATEGORIES;

      return {
        ...state,
        questionText: nextQuestion,
        categories: nextCategories,
        results: buildResults(nextCategories, state.categoryTotalsById),
      };
    }

    case "active_totals": {
      const totals = action.totals;
      const totalAmountCents = Number(totals?.total_amount_cents);
      const totalDonationsCount = Number(totals?.total_donations);

      const categoryTotalsById =
        totals?.category_totals && typeof totals.category_totals === "object"
          ? totals.category_totals
          : state.categoryTotalsById;

      return {
        ...state,
        totalAmountCents: Number.isFinite(totalAmountCents) ? totalAmountCents : state.totalAmountCents,
        totalDonationsCount: Number.isFinite(totalDonationsCount) ? totalDonationsCount : state.totalDonationsCount,
        categoryTotalsById,
        results: buildResults(state.categories, categoryTotalsById),
      };
    }

    // -------------------------------------------------------------------------
    // WEBSOCKET MESSAGES
    // -------------------------------------------------------------------------
    case "ws_message":
      return handleWebSocketMessage(state, action.msg);

    // -------------------------------------------------------------------------
    // SESSION MANAGEMENT
    // -------------------------------------------------------------------------
    case "reset_session":
      return {
        ...state,
        sessionState: SESSION_STATES.IDLE,
        sessionCategoryId: null,
        sessionCategoryName: null,
        sessionCategoryChosenAt: null,
        sessionTotalMoney: 0,
        sessionLastMoneyAt: null,
        sessionDonationData: null,
        sessionDonationCompletedAt: null,
      };

    default:
      return state;
  }
}

// ============================================================================
// WEBSOCKET MESSAGE HANDLERS
// ============================================================================

function handleWebSocketMessage(state, msg) {
  if (!msg || typeof msg !== "object") return state;

  console.log("[Store] WebSocket message:", msg.type, msg.data);

  switch (msg.type) {
    case "category_chosen":
      return handleCategoryChosen(state, msg.data);

    case "money_inserted":
      return handleMoneyInserted(state, msg.data);

    case "donation_created":
      return handleDonationCreated(state, msg.data);

    default:
      console.warn("[Store] Unknown message type:", msg.type);
      return state;
  }
}

function handleCategoryChosen(state, data) {
  const categoryId = data?.category_id;
  const categoryName = data?.category_name;

  console.log("[Store] Category chosen:", categoryName);

  // If we already have money in session, merge the category
  if (state.sessionState === SESSION_STATES.COLLECTING_MONEY) {
    console.log("[Store] Merging category with existing money");
    return {
      ...state,
      sessionCategoryId: categoryId,
      sessionCategoryName: categoryName,
      sessionCategoryChosenAt: Date.now(),
    };
  }

  // Start a new session with category
  console.log("[Store] Starting new session with category");
  return {
    ...state,
    sessionState: SESSION_STATES.CATEGORY_CHOSEN,
    sessionCategoryId: categoryId,
    sessionCategoryName: categoryName,
    sessionCategoryChosenAt: Date.now(),
    sessionTotalMoney: 0,
    sessionLastMoneyAt: null,
    sessionDonationData: null,
    sessionDonationCompletedAt: null,
  };
}

function handleMoneyInserted(state, data) {
  const amountAdded = data?.amount_cents || 0;

  console.log("[Store] Money inserted:", amountAdded, "cents");

  // If no session yet, start one with money (waiting for category)
  if (state.sessionState === SESSION_STATES.IDLE) {
    console.log("[Store] Starting new session with money");
    return {
      ...state,
      sessionState: SESSION_STATES.COLLECTING_MONEY,
      sessionTotalMoney: amountAdded,
      sessionLastMoneyAt: Date.now(),
    };
  }

  // Add to existing session
  const newTotal = (state.sessionTotalMoney || 0) + amountAdded;
  console.log("[Store] Adding to session:", amountAdded, "→ Total:", newTotal);

  return {
    ...state,
    sessionState: SESSION_STATES.COLLECTING_MONEY,
    sessionTotalMoney: newTotal,
    sessionLastMoneyAt: Date.now(),
  };
}

function handleDonationCreated(state, data) {
  console.log("[Store] Donation created:", data.amount_cents, "cents");

  const totals = data?.totals ?? {};
  const totalAmountCents = Number(totals.total_amount_cents);
  const totalDonationsCount = Number(totals.total_donations);

  const categoryTotalsById =
    totals.category_totals && typeof totals.category_totals === "object"
      ? totals.category_totals
      : state.categoryTotalsById;

  const amountCents = Number(data.amount_cents);

  // Update totals & recent donations
  const updatedState = {
    ...state,
    totalAmountCents: Number.isFinite(totalAmountCents) ? totalAmountCents : state.totalAmountCents,
    totalDonationsCount: Number.isFinite(totalDonationsCount) ? totalDonationsCount : state.totalDonationsCount,
    categoryTotalsById,
    recentDonationsCents:
      Number.isFinite(amountCents) && amountCents > 0
        ? clampRecent([amountCents, ...state.recentDonationsCents], 3)
        : state.recentDonationsCents,
    results: buildResults(state.categories, categoryTotalsById),
  };

  // Update session if active
  if (state.sessionState === SESSION_STATES.IDLE) {
    console.warn("[Store] Donation created but session is IDLE - only updating totals");
    return updatedState;
  }

  // Resolve category name from categories if not in session
  let categoryName = state.sessionCategoryName;
  if (!categoryName && data.category_id) {
    const category = state.categories.find((c) => c.id === data.category_id);
    if (category) {
      categoryName = category.name;
      console.log("[Store] Resolved category name:", categoryName);
    } else {
      categoryName = `Kategorie ${data.category_id}`;
    }
  }

  console.log("[Store] Session complete - donation:", amountCents, "cents for", categoryName);

  return {
    ...updatedState,
    sessionState: SESSION_STATES.DONATION_COMPLETE,
    sessionCategoryId: data.category_id,
    sessionCategoryName: categoryName,
    sessionDonationData: data,
    sessionDonationCompletedAt: Date.now(),
  };
}
