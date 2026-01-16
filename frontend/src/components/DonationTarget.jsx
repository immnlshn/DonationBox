export default function DonationTarget({ charityName }) {
  return (
    <section className="donation-target">
      <p className="target-text">
        Die Spenden werden gesammelt für: <strong>{charityName}</strong>
      </p>
    </section>
  );
}
