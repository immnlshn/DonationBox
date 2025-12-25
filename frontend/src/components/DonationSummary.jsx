export default function DonationSummary({ recentDonations, totalAmount, totalDonationsCount }) {
    return (
        <section className="donation-summary">
            <div className="recent-donations">
                <h3 className="subtitle">Aktuelle Spenden:</h3>
                <ul className="donation-list">
                    {recentDonations.map((donation, index) => (
                        <li key={`${donation}-${index}`}>{donation}</li>
                    ))}
                </ul>
            </div>

            <p className="total-amount">
                Wir haben bereits insgesamt <strong>${totalAmount}</strong> mit{' '}
                <strong>{totalDonationsCount}</strong> Spenden gesammelt.
            </p>
        </section>
    );
}