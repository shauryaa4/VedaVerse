import './ConfidenceBadge.css';

/**
 * N-D5-04 / CONF-01→05 badge contract.
 *
 * `confidence` is RagResponse.confidence ("high" | "medium" | "low").
 * `abstained` is RagResponse.abstained. These are checked separately (not
 * folded into one field) because the backend can set confidence: "low"
 * *and* abstained: true at once — per N-D5-04's own spec, ABSTAIN must
 * read as a distinct "no answer" state, not just the low-confidence color
 * with different text, so `abstained` always wins regardless of what
 * `confidence` says.
 */
export default function ConfidenceBadge({ confidence, abstained }) {
  if (abstained) {
    return <span className="confidence-badge confidence-badge--abstain">No answer</span>;
  }

  const level = confidence || 'low';
  const labels = { high: 'High confidence', medium: 'Medium confidence', low: 'Low confidence' };

  return (
    <span className={`confidence-badge confidence-badge--${level}`}>
      {labels[level] || level}
    </span>
  );
}
