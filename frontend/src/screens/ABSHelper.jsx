import { useEffect } from 'react';
import ErrorNotice from '../components/ErrorNotice.jsx';
import './ABSHelper.css';

/**
 * N-D4-04/05 — ABS Helper tab.
 *
 * Matches the real backend model exactly (backend/models/abs_models.py,
 * ABSAssessment): relevance ("likely"|"possible"|"unlikely"|
 * "not_applicable"), reasoning[], applicable_authority_guidance[],
 * ip_filing_flag + ip_filing_note, disclaimer. There is no `checklist`
 * field on the real model (that was the original build-spec sketch) —
 * `reasoning` and `applicable_authority_guidance` are what the backend
 * actually returns, so those are what render here.
 *
 * Auto-populates the first time this tab is opened (lazy, same pattern as
 * TKDLSearch) — no re-asking the user anything, per N-D4-05. disclaimer
 * is rendered verbatim, same rule as TKDL's.
 */
export default function ABSHelper({ state, onFetch, onRestart }) {
  const { data, loading, error, fetched } = state;

  useEffect(() => {
    if (!fetched && !loading) onFetch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="abs-helper">
      <div className="abs-helper__banner">
        ABS Helper — DEMO. Not a live filing status check. No NBA/State Biodiversity Board
        integration.
      </div>

      {loading && <p className="abs-helper__status">Checking Access &amp; Benefit-Sharing relevance…</p>}
      {/* Part 4 fix: same dead-end issue as TKDLSearch — give a retry path
          that doesn't require leaving the tab. */}
      <ErrorNotice error={error} onRetry={onFetch} onRestart={onRestart} retryLabel="Re-check" />

      {data && (
        <div className="abs-helper__card card">
          <span className={`abs-helper__relevance abs-helper__relevance--${data.relevance}`}>
            {data.relevance.replace('_', ' ').toUpperCase()}
          </span>

          {data.reasoning?.length > 0 && (
            <ul className="abs-helper__list">
              {data.reasoning.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          )}

          {data.applicable_authority_guidance?.length > 0 && (
            <div className="abs-helper__section">
              <p className="abs-helper__section-title">Who to check with</p>
              <ul className="abs-helper__list">
                {data.applicable_authority_guidance.map((g, i) => (
                  <li key={i}>{g}</li>
                ))}
              </ul>
            </div>
          )}

          {data.ip_filing_flag && (
            <div className="abs-helper__flag">
              <p>
                {data.ip_filing_note ||
                  'This may trigger a pre-IP-filing approval requirement under Section 6 of the Biological Diversity Act.'}
              </p>
            </div>
          )}

          <p className="abs-helper__disclaimer">{data.disclaimer}</p>

          <button type="button" className="abs-helper__refresh" onClick={onFetch} disabled={loading}>
            Re-check
          </button>
        </div>
      )}
    </div>
  );
}
