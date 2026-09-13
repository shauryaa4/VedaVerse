import { CATEGORY_LABELS } from '../data/options.js';
import './ClassificationResult.css';

/**
 * FE-05. Renders exactly what POST /classify returned — nothing here is
 * re-derived or guessed on the frontend. Per build spec §4: "Never present
 * this as LLM-generated — it's a deterministic function, say so if asked."
 */
export default function ClassificationResult({ classification, onContinue, onBack }) {
  if (!classification) return null;

  const { category, reasons, confidence, unresolved_flags: unresolvedFlags } = classification;
  const label = CATEGORY_LABELS[category] || category;

  return (
    <div className="classification">
      <div className="classification__card card">
        <p className="classification__eyebrow">Deterministic rule engine — not an AI guess</p>
        <h2 className="classification__category">{label}</h2>
        <span className={`classification__badge classification__badge--${confidence}`}>
          {confidence?.toUpperCase()} confidence
        </span>

        {reasons?.length > 0 && (
          <ul className="classification__reasons">
            {reasons.map((reason, i) => (
              <li key={i}>{reason}</li>
            ))}
          </ul>
        )}

        {unresolvedFlags?.length > 0 && (
          <div className="classification__flags">
            <p className="classification__flags-title">Flagged for your review</p>
            <ul>
              {unresolvedFlags.map((flag, i) => (
                <li key={i}>{flag}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="classification__actions">
          <button type="button" className="classification__back" onClick={onBack}>
            Back to questionnaire
          </button>
          <button type="button" className="classification__continue" onClick={onContinue}>
            Continue to Q&amp;A
          </button>
        </div>
      </div>
    </div>
  );
}
