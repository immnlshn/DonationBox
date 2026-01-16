import "./App.css";

import DonationQuestion from "./components/DonationQuestion.jsx";
import DonationSummary from "./components/DonationSummary.jsx";
import DonationTarget from "./components/DonationTarget.jsx";
import QRCodeInfo from "./components/QRCodeInfo.jsx";
import CallToDonate from "./components/CallToDonate.jsx";
import VotingResultsChart from "./components/VotingResultsChart.jsx";

import qrCodeSvg from "./assets/qrcode.svg";

export default function App() {
  // Hardcoded values for demonstration, can be replaced with dynamic data
  const questionText = "Wer ist der GOAT im Fußball?";

  const recentDonations = ["1 €", "2 €", "0,50 €"];
  const totalAmount = "97,25 €";
  const totalDonationsCount = 105;

  const charityName = "Tierheim Dellbrück e.V.";

  const qrInfoText =
    "Scannen Sie den QR-Code, um mehr über die Spendenorganisation zu erfahren.";

  const callToActionText = "Unterstützen Sie unsere Sache heute!";

  const results = [
    { name: "Lionel Messi", amount: "65,00 €", percent: 70 },
    { name: "Cristiano Ronaldo", amount: "32,25 €", percent: 35 },
  ];

  return (
    <div className="main-page">
      <DonationQuestion text={questionText} />

      <DonationSummary
        recentDonations={recentDonations}
        totalAmount={totalAmount}
        totalDonationsCount={totalDonationsCount}
      />

      <DonationTarget charityName={charityName} />

      <QRCodeInfo
        qrImageSrc={qrCodeSvg}
        qrInfoText={qrInfoText}
        alt="QR Code for more information"
      />

      <CallToDonate text={callToActionText} />

      <VotingResultsChart results={results} />
    </div>
  );
}
