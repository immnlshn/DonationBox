import { useEffect, useMemo, useReducer } from "react";
import { createWsClient } from "../services/wsClient";
import { getActiveVote, getActiveVoteTotals } from "../services/apiClient";
import { initialState, applyActiveVote, applyActiveTotals, reduceWsMessage } from "./donationsState";

/**
 * Hook that:
 * 1) Hydrates UI via REST (active vote + totals) so the screen is correct after reload
 * 2) Subscribes to WebSocket broadcasts for live updates
 *
 * If there is no active vote yet, REST calls may return 404; we keep the fallback UI.
 */
export function useDonationsWs() {
  const [state, dispatch] = useReducer((s, action) => {
    if (action.type === "conn") return { ...s, connection: action.status };
    if (action.type === "active_vote") return applyActiveVote(s, action.vote);
    if (action.type === "active_totals") return applyActiveTotals(s, action.totals);
    if (action.type === "ws") return reduceWsMessage(s, action.msg);
    return s;
  }, initialState);

  const wsUrl = import.meta.meta.env.VITE_WS_URL;

  const client = useMemo(() => {
    return createWsClient({
      url: wsUrl,
      onStatus: (status) => dispatch({ type: "conn", status }),
      onMessage: (msg) => dispatch({ type: "ws", msg }),
    });
  }, [wsUrl]);

  useEffect(() => {
    // REST hydration (OpenAPI)
    (async () => {
      try {
        const vote = await getActiveVote();
        dispatch({ type: "active_vote", vote });
      } catch (e) {
        // Expected if there is no active vote (404)
        console.warn("GET /voting/active failed:", e?.message ?? e);
      }

      try {
        const totals = await getActiveVoteTotals();
        dispatch({ type: "active_totals", totals });
      } catch (e) {
        // Expected if there is no active vote (404)
        console.warn("GET /voting/active/totals failed:", e?.message ?? e);
      }
    })();

    // WebSocket subscription for live donation updates
    client.connect();
    return () => client.close();
  }, [client]);

  return state;
}
