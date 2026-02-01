/**
 * Custom Hook: useDonationStore
 *
 * Provides unified state management for donations:
 * - WebSocket connection & messages
 * - REST API hydration
 * - Session state for popups
 * - Totals & statistics
 */

import { useEffect, useReducer } from "react";
import { createWsClient } from "../services/wsClient";
import { getActiveVote, getActiveVoteTotals } from "../services/votingApi";
import { initialState, reducer } from "./donationStore";

export function useDonationStore() {
  const [state, dispatch] = useReducer(reducer, initialState);

  const wsUrl = import.meta.env.VITE_WS_URL;

  useEffect(() => {
    console.log("[useDonationStore] Initializing...");

    // Create WebSocket client
    const client = createWsClient({
      url: wsUrl,
      onStatus: (status) => {
        console.log("[useDonationStore] Connection status:", status);
        dispatch({ type: "connection", status });
      },
      onMessage: (msg) => {
        console.log("[useDonationStore] WebSocket message:", msg.type);
        dispatch({ type: "ws_message", msg });
      },
    });

    // REST API hydration
    (async () => {
      try {
        console.log("[useDonationStore] Fetching active vote...");
        const vote = await getActiveVote();
        dispatch({ type: "active_vote", vote });
        console.log("[useDonationStore] Active vote loaded:", vote.question);
      } catch (e) {
        console.warn("[useDonationStore] GET /voting/active failed:", e?.message ?? e);
      }

      try {
        console.log("[useDonationStore] Fetching active totals...");
        const totals = await getActiveVoteTotals();
        dispatch({ type: "active_totals", totals });
        console.log("[useDonationStore] Active totals loaded:", totals.total_amount_cents, "cents");
      } catch (e) {
        console.warn("[useDonationStore] GET /voting/active/totals failed:", e?.message ?? e);
      }
    })();

    // Connect WebSocket
    client.connect();

    // Cleanup on unmount
    return () => {
      console.log("[useDonationStore] Cleaning up...");
      client.close();
    };
  }, []); // Empty deps: re-fetch on every mount

  // Helper function to end session
  const endSession = () => {
    console.log("[useDonationStore] Ending session");
    dispatch({ type: "reset_session" });
  };

  return {
    ...state,
    endSession,
  };
}
