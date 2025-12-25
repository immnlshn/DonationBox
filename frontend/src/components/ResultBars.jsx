export default function VotingResultsChart({ results }) {
  return (
    <section className="voting-results-chart">
      {results.map((candidate) => (
        <CandidateResultColumn
          key={candidate.name}
          name={candidate.name}
          amount={candidate.amount}
          percent={candidate.percent}
        />
      ))}
    </section>
  );
}

function CandidateResultColumn({ name, amount, percent }) {
  const safePercent = Math.max(0, Math.min(100, Number(percent) || 0));

  return (
    <div className="candidate-result-column">
      <div className="bar">
        <div className="fill" style={{ height: `${safePercent}%` }}>
          <span className="bar-label">{amount}</span>
        </div>
      </div>
      <span className="candidate-name">{name}</span>
    </div>
  );
}
