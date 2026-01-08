import "./App.css";

import DonationQuestion from "./components/DonationQuestion.jsx";
import DonationSummary from "./components/DonationSummary.jsx";
import DonationTarget from "./components/DonationTarget.jsx";
import QRCodeInfo from "./components/QRCodeInfo.jsx";
import CallToDonate from "./components/CallToDonate.jsx";
import VotingResultsChart from "./components/ResultBars.jsx";

import clubLogo from "./assets/logo.png"; // bleibt für QRCodeInfo
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

  // NUR Prozent für die Balken
  const results = [
    { name: "Lionel Messi", percent: 70.5 },
    { name: "Cristiano Ronaldo", percent: 29.5 },
  ];

  return (
    <div className="page">
      <header className="header">
        <div className="brand">
          {/* Logo oben entfernt, Text bleibt */}
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
        <section className="card card-hero">
          <DonationQuestion text={questionText} />
        </section>

        <section className="card">
          {/* Damit der Satz "Wir haben bereits ..." nicht erscheint:
              totalAmount/totalDonationsCount nicht an DonationSummary übergeben */}
          <DonationSummary recentDonations={recentDonations} />
        </section>

        <section className="card">
          <div className="donation-info">
            <DonationTarget charityName={charityName} />
            <QRCodeInfo
              qrImageSrc={qrCodeSvg}
              clubLogoSrc={clubLogo}
              qrInfoText={qrInfoText}
              alt="QR Code for more information"
            />
          </div>
        </section>

        <section className="card card-cta">
          <CallToDonate text={callToActionText} />
        </section>

        <section className="card">
          <div className="section-head">
            <h2 className="section-title">Aktueller Stand</h2>
            {/* "Ergebnis der Abstimmung (in Prozent)" entfernt */}
          </div>
          <VotingResultsChart results={results} />
        </section>
      </main>
    </div>
  );
}
