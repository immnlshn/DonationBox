import "./App.css";

import DonationQuestion from "./components/DonationQuestion.jsx";
import DonationSummary from "./components/DonationSummary.jsx";
import DonationTarget from "./components/DonationTarget.jsx";
import QRCodeInfo from "./components/QRCodeInfo.jsx";
import CallToDonate from "./components/CallToDonate.jsx";
import VotingResultsChart from "./components/VotingResultsChart.jsx";
import DonationSessionPopup from "./components/DonationSessionPopup.jsx";

import clubLogo from "./assets/logo.png";
import qrCodeSvg from "./assets/qrcode.svg";

import { useDonationStore } from "./state/useDonationStore";
import { centsToEuroString } from "./state/donationStore";

export default function App() {
  // Static UI text (not backend-driven)
  const charityName = "Lobby für Mädchen- Mädchenhaus Köln e.V.";
  const qrInfoText =
    "Scannen Sie den QR-Code, um mehr über die Spendenorganisation zu erfahren.";
  const callToActionText = "Spenden Sie Ihr Bargeld und stimmen Sie ab!";

  // Dynamic state from unified store
  const store = useDonationStore();
  const {
    totalAmountCents,
    totalDonationsCount,
    recentDonationsCents,
    questionText,
    results,
    endSession,
  } = store;

  // Session state for popup
  const sessionState = {
    sessionState: store.sessionState,
    categoryId: store.sessionCategoryId,
    categoryName: store.sessionCategoryName,
    categoryChosenAt: store.sessionCategoryChosenAt,
    totalMoneyInSession: store.sessionTotalMoney,
    lastMoneyInsertedAt: store.sessionLastMoneyAt,
    donationData: store.sessionDonationData,
    donationCompletedAt: store.sessionDonationCompletedAt,
  };

  const totalAmount = centsToEuroString(totalAmountCents);
  const recentDonations = recentDonationsCents.map(centsToEuroString);

  return (
    <div className="page">
      {/* Session-based Popup - stays open throughout donation flow */}
      <DonationSessionPopup session={sessionState} onSessionEnd={endSession} />

      <header className="header">
        <div className="brand">
          <div className="brand-text">
            <div className="brand-title">Spendenbasierte Abstimmung</div>
            <div className="brand-subtitle">Projekt von Studenten der UzK</div>
          </div>
        </div>

        <div className="stats">
          <div className="stat">
            <div className="stat-label">Gesamt</div>
            <div className="stat-value">{totalAmount}</div>
          </div>
          <div className="stat">
            <div className="stat-label">Spenden</div>
            <div className="stat-value">{totalDonationsCount}</div>
          </div>
        </div>
      </header>

      <main className="stack">
          <section className="card card-cta">
              <CallToDonate text={callToActionText} />
          </section>
        <section className="card card-hero">
          {/* Comes from GET /voting/active if available; otherwise a generic fallback */}
          <DonationQuestion text={questionText} />
        </section>
          <section className="card">
              <div className="section-head">
                  <h2 className="section-title">Aktueller Stand</h2>
              </div>

              <VotingResultsChart results={results} />
          </section>

        <section className="card">
          <DonationSummary recentDonations={recentDonations} />
        </section>

        <section className="card">
          <div className="donation-info">
            <QRCodeInfo
              qrImageSrc={qrCodeSvg}
              clubLogoSrc={clubLogo}
              qrInfoText={qrInfoText}
              alt="QR Code for more information"
            >
              <DonationTarget charityName={charityName} />
            </QRCodeInfo>
          </div>
        </section>





      </main>
    </div>
  );
}
