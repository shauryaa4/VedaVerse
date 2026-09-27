import { useState } from 'react';
import ErrorNotice from '../components/ErrorNotice.jsx';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';
import './JurisdictionSelect.css';

export default function JurisdictionSelect({ onSelect, loading, error, onRestart, currentLang = 'en' }) {
  const [pending, setPending] = useState(null);
  const uiText = useTranslatedTexts([
    'Select Jurisdiction', 'Choose the jurisdiction applicable for your product assessment:',
    'India', 'International', 'Products intended primarily for protection or market entry in India.',
    'Products seeking international patent or PCT pathways.', 'Saving…',
  ], currentLang);

  const handlePick = (value) => {
    setPending(value);
    onSelect(value);
  };

  return (
    <div className="jurisdiction">
      <h2 className="jurisdiction__title">{uiText('Select Jurisdiction')}</h2>
      <p className="jurisdiction__subtitle">
        {uiText('Choose the jurisdiction applicable for your product assessment:')}
      </p>

      <ErrorNotice error={error} onRestart={onRestart} currentLang={currentLang} />

      <div className="jurisdiction__options">
        <button
          type="button"
          className="jurisdiction__option card"
          onClick={() => handlePick('india')}
          disabled={loading}
        >
          <span className="jurisdiction__option-title">{uiText('India')}</span>
          <span className="jurisdiction__option-desc">
            {uiText('Products intended primarily for protection or market entry in India.')}
          </span>
          {loading && pending === 'india' && (
            <span className="jurisdiction__option-loading">{uiText('Saving…')}</span>
          )}
        </button>

        <button
          type="button"
          className="jurisdiction__option card"
          onClick={() => handlePick('international')}
          disabled={loading}
        >
          <span className="jurisdiction__option-title">{uiText('International')}</span>
          <span className="jurisdiction__option-desc">
            {uiText('Products seeking international patent or PCT pathways.')}
          </span>
          {loading && pending === 'international' && (
            <span className="jurisdiction__option-loading">{uiText('Saving…')}</span>
          )}
        </button>
      </div>
    </div>
  );
}
