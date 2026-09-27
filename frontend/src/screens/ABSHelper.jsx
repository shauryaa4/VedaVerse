import { useEffect } from 'react';
import ErrorNotice from '../components/ErrorNotice.jsx';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';
import './ABSHelper.css';

export default function ABSHelper({ state, onFetch, onRestart, currentLang = 'en' }) {
  const { data, loading, error, fetched } = state;
  const uiText = useTranslatedTexts([
    'ABS-aware guidance · Not a live NBA/SBB filing or status service.',
    'Checking Access & Benefit-Sharing relevance…', 'Re-check', 'Who to check with',
    'This may trigger a pre-IP-filing approval requirement under Section 6 of the Biological Diversity Act.',
    data?.relevance?.replace(/_/g, ' ')?.toUpperCase(), data?.disclaimer,
    data?.ip_filing_note, ...(data?.reasoning || []), ...(data?.applicable_authority_guidance || []),
  ], currentLang);

  useEffect(() => {
    if (!fetched && !loading) onFetch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="abs-helper">
      <div className="abs-helper__banner">
        {uiText('ABS-aware guidance · Not a live NBA/SBB filing or status service.')}
      </div>

      {loading && <p className="abs-helper__status">{uiText('Checking Access & Benefit-Sharing relevance…')}</p>}
      <ErrorNotice error={error} onRetry={onFetch} onRestart={onRestart} retryLabel={uiText('Re-check')} currentLang={currentLang} />

      {data && (
        <div className="abs-helper__card card">
          <span className={`abs-helper__relevance abs-helper__relevance--${data.relevance}`}>
            {uiText(data.relevance?.replace('_', ' ')?.toUpperCase())}
          </span>

          {data.reasoning?.length > 0 && (
            <ul className="abs-helper__list">
              {data.reasoning.map((r, i) => (
                <li key={i}>{uiText(r)}</li>
              ))}
            </ul>
          )}

          {data.applicable_authority_guidance?.length > 0 && (
            <div className="abs-helper__section">
              <p className="abs-helper__section-title">{uiText('Who to check with')}</p>
              <ul className="abs-helper__list">
                {data.applicable_authority_guidance.map((g, i) => (
                  <li key={i}>{uiText(g)}</li>
                ))}
              </ul>
            </div>
          )}

          {data.ip_filing_flag && (
            <div className="abs-helper__flag">
              <p>
                {uiText(
                  data.ip_filing_note ||
                    'This may trigger a pre-IP-filing approval requirement under Section 6 of the Biological Diversity Act.'
                )}
              </p>
            </div>
          )}

          <p className="abs-helper__disclaimer">{uiText(data.disclaimer)}</p>

          <button type="button" className="abs-helper__refresh" onClick={onFetch} disabled={loading}>
            {uiText('Re-check')}
          </button>
        </div>
      )}
    </div>
  );
}
