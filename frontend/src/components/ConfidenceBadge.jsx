import './ConfidenceBadge.css';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';

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
export default function ConfidenceBadge({ confidence, score, abstained, currentLang = 'en' }) {
  const uiText = useTranslatedTexts(['No answer', 'High confidence', 'Medium confidence', 'Low confidence'], currentLang);
  if (abstained) {
    return <span className="confidence-badge confidence-badge--abstain">{uiText('No answer')}</span>;
  }

  const level = confidence || 'low';
  const labels = { high: 'High confidence', medium: 'Medium confidence', low: 'Low confidence' };
  const pct = typeof score === 'number' ? Math.round(score * 100) : null;

  return (
    <span className={`confidence-badge confidence-badge--${level}`}>
      {uiText(labels[level] || level)}
      {pct !== null && <span className="confidence-badge__pct">{pct}%</span>}
    </span>
  );
}
