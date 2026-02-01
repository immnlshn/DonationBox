import Popup from "./Popup";

/**
 * Money Inserted Notification
 * Shows amount inserted and current total
 */
export default function MoneyInsertedNotification({ isOpen, onClose, data }) {
  if (!data) return null;

  const amountEuro = (data.amount_cents / 100).toFixed(2).replace(".", ",");
  const totalEuro = (data.total_amount_cents / 100).toFixed(2).replace(".", ",");

  return (
    <Popup
      isOpen={isOpen}
      onClose={onClose}
      autoCloseMs={2500}
      type="success"
    >
      <div className="popup-content">
        <h2 className="popup-header popup-text-highlight">
          💰 Geld eingefügt
        </h2>
        <p className="popup-body popup-text-center popup-text-large">
          <strong>+{amountEuro} €</strong> eingefügt
        </p>
        <p className="popup-body popup-text-center" style={{ color: "var(--muted)" }}>
          Gesamtbetrag: <strong>{totalEuro} €</strong>
        </p>
      </div>
    </Popup>
  );
}
