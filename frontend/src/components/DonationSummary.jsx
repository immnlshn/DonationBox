export default function DonationSummary({ recentDonations }) {
  return (
    <section className="donation-summary">
      <div className="recent-donations">
        <h3 className="subtitle">Letzten Spenden</h3>
        <ul className="donation-list">
          {recentDonations.map((donation, index) => (
            <li key={`${donation}-${index}`}>{donation}</li>
          ))}
        </ul>
      </div>
    </section>
  );
}
