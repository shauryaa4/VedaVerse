import './ConfidencePanel.css';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';

/**
 * Numeric confidence, drawn: a gauge for the overall score and a breakdown of
 * the three weighted signals behind it (RagResponse.confidence_score and
 * RagResponse.confidence_breakdown from POST /query).
 *
 * The score measures evidence quality (citation support, classification
 * certainty, source coverage). The badge level ALSO applies safety gates
 * (e.g. a treaty that is not yet in force caps the level at Medium), so the
 * backend's confidence_reason is shown underneath to explain the level.
 *
 * Pure SVG/CSS -- no chart library.
 */

const SEGMENT_OPACITY = [1, 0.68, 0.42];

function Gauge({ pct, level }) {
  // pathLength=100 lets dasharray/dashoffset be expressed directly in percent.
  return (
    <svg
      className={`confidence-gauge confidence-gauge--${level}`}
      viewBox="0 0 140 84"
      role="img"
      aria-label={`Confidence score ${pct} percent`}
    >
      <path className="confidence-gauge__track" d="M 18 74 A 52 52 0 0 1 122 74" pathLength="100" />
      <path
        className="confidence-gauge__value"
        d="M 18 74 A 52 52 0 0 1 122 74"
        pathLength="100"
        strokeDasharray="100"
        strokeDashoffset={100 - pct}
      />
      <text className="confidence-gauge__pct" x="70" y="66" textAnchor="middle">
        {pct}%
      </text>
    </svg>
  );
}

export default function ConfidencePanel({
  score,
  breakdown = [],
  level = 'low',
  reason,
  currentLang = 'en',
  showGauge = true,
}) {
  const uiText = useTranslatedTexts(
    [
      'Confidence score',
      'How this score is built',
      'Citation support',
      'Classification certainty',
      'Source coverage',
      'weight',
      'Why this level',
      reason,
    ],
    currentLang
  );

  if (typeof score !== 'number') return null;

  const pct = Math.round(score * 100);
  const hasBreakdown = Array.isArray(breakdown) && breakdown.length > 0;

  return (
    <div className={`confidence-panel confidence-panel--${level}`}>
      {showGauge && (
        <div className="confidence-panel__gauge">
          <Gauge pct={pct} level={level} />
          <p className="confidence-panel__gauge-label">{uiText('Confidence score')}</p>
        </div>
      )}

      {hasBreakdown && (
        <div className="confidence-panel__breakdown">
          <p className="confidence-panel__title">{uiText('How this score is built')}</p>

          {/* Stacked bar: each signal's contribution, in points of the final score. */}
          <div className="confidence-stack" role="img" aria-label={`Score built from ${breakdown.length} signals`}>
            {breakdown.map((c, i) => (
              <span
                key={c.key}
                className="confidence-stack__segment"
                style={{
                  width: `${c.contribution * 100}%`,
                  opacity: SEGMENT_OPACITY[i % SEGMENT_OPACITY.length],
                }}
                title={`${uiText(c.label)}: +${Math.round(c.contribution * 100)} pts`}
              />
            ))}
          </div>

          <ul className="confidence-rows">
            {breakdown.map((c, i) => (
              <li key={c.key} className="confidence-row" title={c.detail}>
                <div className="confidence-row__head">
                  <span
                    className="confidence-row__dot"
                    style={{ opacity: SEGMENT_OPACITY[i % SEGMENT_OPACITY.length] }}
                  />
                  <span className="confidence-row__label">{uiText(c.label)}</span>
                  <span className="confidence-row__weight">
                    {uiText('weight')} {Math.round(c.weight * 100)}%
                  </span>
                  <strong className="confidence-row__value">{Math.round(c.value * 100)}%</strong>
                  <span className="confidence-row__pts">+{Math.round(c.contribution * 100)}</span>
                </div>
                <div className="confidence-row__bar">
                  <span
                    className="confidence-row__fill"
                    style={{
                      width: `${c.value * 100}%`,
                      opacity: SEGMENT_OPACITY[i % SEGMENT_OPACITY.length],
                    }}
                  />
                </div>
              </li>
            ))}
          </ul>

          {reason && (
            <p className="confidence-panel__reason">
              <strong>{uiText('Why this level')}:</strong> {uiText(reason)}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
