import Popup from "./Popup";
import balloons from "../assets/balloons.png";

/**
 * Thank You Popup - shown after donation is completed
 * Automatically closes after 5 seconds
 */
export default function ThankYouNotification({ isOpen, onClose, donationData }) {
  if (!donationData) return null;

  const amountEuro = (donationData.amount_cents / 100).toFixed(2).replace(".", ",");
  const categoryName = donationData.category_name || "die gewählte Kategorie";

  return (
    <Popup
      isOpen={isOpen}
      onClose={onClose}
      autoCloseMs={5000}
      type="success"
    >
      <div className="popup-content">
        <h1 className="popup-header">Vielen Dank für Ihre Spende!</h1>
        <img
          src={balloons}
          alt="Celebration balloons"
          className="popup-image"
        />
        <p className="popup-body popup-text-center popup-text-large">
          Sie haben <strong>{amountEuro} €</strong> für "<strong>{categoryName}</strong>" gespendet.
        </p>
      </div>
      <div className="popup-footer popup-text-center">
        <p style={{ margin: 0 }}>
          Ihre Unterstützung hilft uns, einen positiven Einfluss zu erzielen.
        </p>
      </div>
    </Popup>
  );
}
