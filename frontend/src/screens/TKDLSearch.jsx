import { useEffect } from 'react';
import ErrorNotice from '../components/ErrorNotice.jsx';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';
import './TKDLSearch.css';

export default function TKDLSearch({ state, onFetch, onRestart, currentLang = 'en' }) {
  const { data, loading, error, fetched } = state;
  const assessment = data?.assessment;
  const uiText = useTranslatedTexts([
    'Offline archive of source-derived records. Not connected to the live Traditional Knowledge Digital Library.',
    'Checking the offline source-derived record archive…', 'Re-check', 'overlap risk',
    'Closest match:', 'Already documented', 'Appears different', 'Potential novel features',
    'All candidate records', 'No matches in this archive for this composition.',
    'ingredient overlap', 'Matched:', 'In record, not yours:',
    assessment?.risk_level?.toUpperCase(), assessment?.disclaimer,
    ...(assessment?.reasoning || []), ...(assessment?.what_was_already_known || []),
    ...(assessment?.what_appears_different || []), ...(assessment?.potential_novel_features || []),
  ], currentLang);

  useEffect(() => {
    if (!fetched && !loading) onFetch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="tkdl">
      <div className="tkdl__banner">
        {uiText('Offline archive of source-derived records. Not connected to the live Traditional Knowledge Digital Library.')}
      </div>

      {loading && <p className="tkdl__status">{uiText('Checking the offline source-derived record archive…')}</p>}
      <ErrorNotice error={error} onRetry={onFetch} onRestart={onRestart} retryLabel={uiText('Re-check')} currentLang={currentLang} />

      {data && (
        <>
          <div className="tkdl__assessment card">
            <span className={`tkdl__risk tkdl__risk--${data.assessment.risk_level}`}>
              {uiText(data.assessment.risk_level?.toUpperCase())} {uiText('overlap risk')}
            </span>

            {data.assessment.closest_record && (
              <p className="tkdl__closest">
                {uiText('Closest match:')} <strong>{data.assessment.closest_record.formulation_name}</strong>{' '}
                ({data.assessment.closest_record.record_id}, {data.assessment.closest_record.source_text})
              </p>
            )}

            {data.assessment.reasoning?.length > 0 && (
              <ul className="tkdl__list">
                {data.assessment.reasoning.map((r, i) => (
                  <li key={i}>{uiText(r)}</li>
                ))}
              </ul>
            )}

            {data.assessment.what_was_already_known?.length > 0 && (
              <div className="tkdl__section">
                <p className="tkdl__section-title">{uiText('Already documented')}</p>
                <ul className="tkdl__list">
                  {data.assessment.what_was_already_known.map((x, i) => (
                    <li key={i}>{uiText(x)}</li>
                  ))}
                </ul>
              </div>
            )}

            {data.assessment.what_appears_different?.length > 0 && (
              <div className="tkdl__section">
                <p className="tkdl__section-title">{uiText('Appears different')}</p>
                <ul className="tkdl__list">
                  {data.assessment.what_appears_different.map((x, i) => (
                    <li key={i}>{uiText(x)}</li>
                  ))}
                </ul>
              </div>
            )}

            {data.assessment.potential_novel_features?.length > 0 && (
              <div className="tkdl__section">
                <p className="tkdl__section-title">{uiText('Potential novel features')}</p>
                <ul className="tkdl__list">
                  {data.assessment.potential_novel_features.map((x, i) => (
                    <li key={i}>{uiText(x)}</li>
                  ))}
                </ul>
              </div>
            )}

            <p className="tkdl__disclaimer">{uiText(data.assessment.disclaimer)}</p>
          </div>

          <div className="tkdl__matches">
            <p className="tkdl__matches-title">{uiText('All candidate records')} ({data.matches.length})</p>
            {data.matches.length === 0 && (
              <p className="tkdl__status">{uiText('No matches in this archive for this composition.')}</p>
            )}
            {data.matches.map((m) => (
              <div key={m.record.record_id} className="tkdl__match card">
                <p className="tkdl__match-name">
                  {m.record.formulation_name}
                  <span className="tkdl__match-id"> — {m.record.record_id}</span>
                </p>
                <p className="tkdl__match-source">{m.record.source_text}</p>
                <p className="tkdl__match-overlap">
                  {Math.round(m.overlap_ratio * 100)}% {uiText('ingredient overlap')}
                </p>
                {m.matched_ingredient_names.length > 0 && (
                  <p className="tkdl__match-detail">
                    <strong>{uiText('Matched:')}</strong> {m.matched_ingredient_names.join(', ')}
                  </p>
                )}
                {m.unmatched_tkdl_ingredient_names.length > 0 && (
                  <p className="tkdl__match-detail">
                    <strong>{uiText('In record, not yours:')}</strong>{' '}
                    {m.unmatched_tkdl_ingredient_names.join(', ')}
                  </p>
                )}
              </div>
            ))}
          </div>

          <button type="button" className="tkdl__refresh" onClick={onFetch} disabled={loading}>
            {uiText('Re-check')}
          </button>
        </>
      )}
    </div>
  );
}
