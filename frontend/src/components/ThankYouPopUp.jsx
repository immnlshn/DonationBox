import balloons from "../assets/balloons.png";

export default function ThankYouPopUp({donationData}) {
  return (
      <div className="popup">
        <div className="popup-inner">
          <div className="popup-content">
            <h1 className="popup-header">Vielen Dank für Ihre Spende!</h1>
            <img src={balloons} alt="balloons" className="popup-image"/>
            <p className="popup-text-description">Sie haben {donationData.amount}€ für "{donationData.category}"
              gespendet.</p>
          </div>
          <div className="popup-footer">
            <p className="popup-text-muted">Ihre Unterstützung hilft uns, einen positiven Einfluss zu
              erzielen.</p>
          </div>
        </div>
      </div>
  );
}