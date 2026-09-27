import { useState, useEffect } from 'react';
import { CATEGORY_LABELS } from '../data/options.js';
import { translateAsync } from '../utils/translator.js';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';
import './ClassificationResult.css';

export default function ClassificationResult({ classification, onContinue, onBack, currentLang = 'en' }) {
  const { category, reasons, confidence, unresolved_flags: unresolvedFlags } = classification || {};
  const label = CATEGORY_LABELS[category] || category;
  const uiText = useTranslatedTexts([
    label, confidence?.toUpperCase(), 'confidence',
    'Deterministic rule engine — not an AI guess', 'Flagged for your review',
    'Back to Questionnaire', 'Continue to Ask & Explore',
  ], currentLang);

  const [translatedReasons, setTranslatedReasons] = useState(reasons || []);
  const [translatedFlags, setTranslatedFlags] = useState([]);

  useEffect(() => {
    let isMounted = true;

    async function loadTranslations() {
      if (currentLang === 'en') {
        setTranslatedReasons(reasons || []);
        const formattedFlags = (unresolvedFlags || []).map((f) =>
          f.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
        );
        setTranslatedFlags(formattedFlags);
        return;
      }

      // Translate reasons dynamically via Bhashini NMT
      if (reasons?.length > 0) {
        const transList = await Promise.all(
          reasons.map((r) => translateAsync(r, currentLang))
        );
        if (isMounted) setTranslatedReasons(transList);
      }

      // Translate flags dynamically via Bhashini NMT
      if (unresolvedFlags?.length > 0) {
        const formatted = unresolvedFlags.map((f) =>
          f.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
        );
        const transFlags = await Promise.all(
          formatted.map((f) => translateAsync(f, currentLang))
        );
        if (isMounted) setTranslatedFlags(transFlags);
      }
    }

    loadTranslations();

    return () => {
      isMounted = false;
    };
  }, [classification, currentLang, reasons, unresolvedFlags]);

  if (!classification) return null;

  return (
    <div className="classification">
      <div className="classification__card card">
        <p className="classification__eyebrow">
          {uiText('Deterministic rule engine — not an AI guess')}
        </p>
        <h2 className="classification__category">{uiText(label)}</h2>
        <span className={`classification__badge classification__badge--${confidence}`}>
          {uiText(confidence?.toUpperCase())} {uiText('confidence')}
        </span>

        {translatedReasons?.length > 0 && (
          <ul className="classification__reasons">
            {translatedReasons.map((reason, i) => (
              <li key={i}>{reason}</li>
            ))}
          </ul>
        )}

        {translatedFlags?.length > 0 && (
          <div className="classification__flags">
            <p className="classification__flags-title">{uiText('Flagged for your review')}</p>
            <ul>
              {translatedFlags.map((flag, i) => (
                <li key={i}>{flag}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="classification__actions">
          <button type="button" className="classification__back" onClick={onBack}>
            {uiText('Back to Questionnaire')}
          </button>
          <button type="button" className="classification__continue" onClick={onContinue}>
            {uiText('Continue to Ask & Explore')}
          </button>
        </div>
      </div>
    </div>
  );
}
