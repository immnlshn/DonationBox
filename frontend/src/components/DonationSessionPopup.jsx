import { useEffect } from "react";
import { SESSION_STATES } from "../state/donationStore";
import balloons from "../assets/balloons.png";

/**
 * Donation Session Popup
 *
 * A persistent popup that stays open throughout the donation flow:
 * 1. Category chosen - shows category, asks for money
 * 2. Money collecting - live counter updates as coins are inserted
 * 3. Donation complete - thank you message with final amount
 *
 * No user interaction required - automatically transitions based on WebSocket events.
 * Auto-closes only after final thank you message.
 */
export default function DonationSessionPopup({ session, onSessionEnd }) {
  const { sessionState, categoryName, totalMoneyInSession, donationData } = session;

  const isOpen = sessionState !== SESSION_STATES.IDLE;

  console.log("[Popup] Rendering with state:", {
    sessionState,
    categoryName,
    totalMoneyInSession,
    isOpen,
    hasDonationData: !!donationData
  });

  // Auto-close after donation is complete (after 5 seconds)
  useEffect(() => {
    if (sessionState !== SESSION_STATES.DONATION_COMPLETE) return;

    console.log("[Popup] Donation complete - starting 5s auto-close timer");
    const timer = setTimeout(() => {
      console.log("[Popup] Auto-close timer expired - ending session");
      onSessionEnd?.();
    }, 5000);

    return () => {
      console.log("[Popup] Cleanup: clearing auto-close timer");
      clearTimeout(timer);
    };
  }, [sessionState, onSessionEnd]);

  if (!isOpen) return null;

  // Helper to format cents to Euro string
  const formatEuro = (cents) => {
    const euros = (cents / 100).toFixed(2).replace(".", ",");
    return `${euros} €`;
  };

  return (
    <div className="popup-overlay">
      <div className="popup-container popup-info">
        {/* PHASE 1: Category Chosen - Waiting for money */}
        {sessionState === SESSION_STATES.CATEGORY_CHOSEN && (
          <div className="popup-content">
            <h2 className="popup-header">
              Kategorie gewählt
            </h2>
            <p className="popup-body popup-text-center popup-text-large">
              <strong>{categoryName || "Kategorie"}</strong> wurde ausgewählt.
            </p>
            <p className="popup-body popup-text-center" style={{ color: "var(--muted)" }}>
              Bitte werfen Sie jetzt Ihr Bargeld ein.
            </p>
            <div className="popup-waiting-indicator">
              <div className="waiting-spinner"></div>
            </div>
          </div>
        )}

        {/* PHASE 2: Collecting Money - Live counter */}
        {sessionState === SESSION_STATES.COLLECTING_MONEY && (
          <div className="popup-content">
            <h2 className="popup-header popup-text-highlight">
              💰 Geld wird gesammelt
            </h2>
            {categoryName ? (
              <p className="popup-body popup-text-center" style={{ color: "var(--muted)", marginBottom: "0.5rem" }}>
                Für: <strong>{categoryName}</strong>
              </p>
            ) : (
              <p className="popup-body popup-text-center" style={{ color: "var(--muted)", marginBottom: "0.5rem" }}>
                Bitte wählen Sie jetzt eine Kategorie
              </p>
            )}
            <div className="popup-money-counter">
              <div className="money-amount-display">
                {formatEuro(totalMoneyInSession)}
              </div>
            </div>
            {categoryName ? (
              <p className="popup-body popup-text-center" style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
                Weiter Münzen einwerfen oder warten...
              </p>
            ) : (
              <p className="popup-body popup-text-center" style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
                Drücken Sie einen Kategorie-Button
              </p>
            )}
          </div>
        )}

        {/* PHASE 3: Donation Complete - Thank you */}
        {sessionState === SESSION_STATES.DONATION_COMPLETE && donationData && (
          <div className="popup-content">
            <h1 className="popup-header">Vielen Dank für Ihre Spende!</h1>
            <img
              src={balloons}
              alt="Celebration balloons"
              className="popup-image"
            />
            <p className="popup-body popup-text-center popup-text-large">
              Sie haben <strong>{formatEuro(donationData.amount_cents)}</strong> für{" "}
              <strong>"{categoryName || "die gewählte Kategorie"}"</strong> gespendet.
            </p>
            <div className="popup-footer popup-text-center">
              <p style={{ margin: 0 }}>
                Ihre Unterstützung hilft uns, einen positiven Einfluss zu erzielen.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
