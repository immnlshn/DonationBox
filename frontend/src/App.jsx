import "./App.css";

import DonationQuestion from "./components/DonationQuestion.jsx";
import DonationSummary from "./components/DonationSummary.jsx";
import DonationTarget from "./components/DonationTarget.jsx";
import QRCodeInfo from "./components/QRCodeInfo.jsx";
import CallToDonate from "./components/CallToDonate.jsx";
import VotingResultsChart from "./components/ResultBars.jsx";

import clubLogo from "./assets/logo.png";
import qrCodeSvg from "./assets/qrcode.svg";

export default function App() {
  const questionText = "Wer ist der GOAT im Fußball?";

  const recentDonations = ["1€", "2€", "0,50€"];
  const totalAmount = "97,25€";
  const totalDonationsCount = 105;

  const charityName = "Lobby für Mädchen- Mädchenhaus Köln e.V.";
  const qrInfoText =
    "Scannen Sie den QR-Code, um mehr über die Spendenorganisation zu erfahren.";

  const callToActionText = "Spenden Sie Ihr Bargeld und stimmen Sie ab!";

  const results = [
    { name: "Lionel Messi", percent: 70.5 },
    { name: "Cristiano Ronaldo", percent: 29.5 },
  ];

  return (
    <div className="page">
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
        {/* Call to Action – gleicher Stil, nur anderer Ort */}
        <section className="card card-cta">
          <CallToDonate text={callToActionText} />
        </section>

        {/* Frage */}
        <section className="card card-hero">
          <DonationQuestion text={questionText} />
        </section>

        {/* Aktueller Stand */}
        <section className="card">
          <div className="section-head">
            <h2 className="section-title">Aktueller Stand</h2>
          </div>
          <VotingResultsChart results={results} />
        </section>

        {/* Letzte Spenden */}
        <section className="card">
          <DonationSummary recentDonations={recentDonations} />
        </section>

        {/* QR / Spendenziel */}
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
