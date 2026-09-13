import { useState } from 'react';
import './JurisdictionSelect.css';

/**
 * FE-02. Calls onSelect(jurisdiction) which App.jsx turns into a real
 * POST /intake call. Kept as a big, unambiguous either/or choice per build
 * spec §3 Q1 — this is the field the entire routing engine (§5) branches on,
 * so there's no "skip" option here.
 */
export default function JurisdictionSelect({ onSelect, loading, error }) {
  const [pending, setPending] = useState(null);

  const handlePick = (value) => {
    setPending(value);
    onSelect(value);
  };

  return (
    <div className="jurisdiction">
      <h2 className="jurisdiction__title">Which legal framework applies to your question?</h2>
      <p className="jurisdiction__subtitle">
        This decides which corpus your answers are grounded in — India's statutes and rules,
        or international treaties (TRIPS, CBD, Nagoya, WIPO GRATK, PCT). The two are never
        mixed in one answer.
      </p>

      {error && <p className="jurisdiction__error">{error}</p>}

      <div className="jurisdiction__options">
        <button
          type="button"
          className="jurisdiction__option card"
          onClick={() => handlePick('india')}
          disabled={loading}
        >
          <span className="jurisdiction__option-title">India</span>
          <span className="jurisdiction__option-desc">
            Patents Act, Biological Diversity Act, Drugs &amp; Cosmetics Act, FSSAI
            Ayurveda-Aahar, Trade Marks Act
          </span>
          {loading && pending === 'india' && (
            <span className="jurisdiction__option-loading">Saving…</span>
          )}
        </button>

        <button
          type="button"
          className="jurisdiction__option card"
          onClick={() => handlePick('international')}
          disabled={loading}
        >
          <span className="jurisdiction__option-title">International</span>
          <span className="jurisdiction__option-desc">
            TRIPS Agreement, Convention on Biological Diversity, Nagoya Protocol, WIPO
            GRATK Treaty, PCT basics
          </span>
          {loading && pending === 'international' && (
            <span className="jurisdiction__option-loading">Saving…</span>
          )}
        </button>
      </div>
    </div>
  );
}
