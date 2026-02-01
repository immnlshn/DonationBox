import Popup from "./Popup";

/**
 * Category Chosen Notification
 * Shows which category was selected
 */
export default function CategoryChosenNotification({ isOpen, onClose, data }) {
  if (!data) return null;

  const categoryName = data.category_name || `Kategorie ${data.category_id}`;

  return (
    <Popup
      isOpen={isOpen}
      onClose={onClose}
      autoCloseMs={3000}
      type="info"
    >
      <div className="popup-content">
        <h2 className="popup-header">
          Kategorie gewählt
        </h2>
        <p className="popup-body popup-text-center popup-text-large">
          <strong>{categoryName}</strong> wurde ausgewählt.
        </p>
        <p className="popup-body popup-text-center" style={{ color: "var(--muted)" }}>
          Bitte werfen Sie jetzt Ihr Bargeld ein.
        </p>
      </div>
    </Popup>
  );
}
