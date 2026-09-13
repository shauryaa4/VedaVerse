import { useEffect } from 'react';
import './TKDLSearch.css';

/**
 * N-D4-02/03 — TKDL Search tab.
 *
 * IMPLEMENTATION NOTE (differs from the original build-spec free-text
 * search sketch): the real backend endpoint (backend/routes/tkdl_routes.py,
 * POST /tkdl/search) takes only {session_id} — no query string. It runs a
 * fixed ingredient-overlap check between the composition already on the
 * PIP (from the questionnaire) and the mock TKDL dataset, and returns a
 * PriorArtAssessment plus every candidate match. So this is a "run the
 * check" screen, not a search box — matching backend/models/tkdl.py's
 * real shape, not N-D4-01/02's original sketch.
 *
 * Fetches lazily the first time this tab is opened (via the `fetched`
 * flag App.jsx tracks), not on session load — avoids a backend call for
 * a tab the user may never open. A "Re-check" button re-runs it, mainly
 * useful if the questionnaire's composition is later revisited.
 *
 * The DEMONSTRATION DATA banner and every disclaimer below are rendered
 * verbatim — both mirror PriorArtAssessment.disclaimer, hard-coded on the
 * backend per build spec §10/§19/§28, never paraphrased here.
 */
export default function TKDLSearch({ state, onFetch }) {
  const { data, loading, error, fetched } = state;

  useEffect(() => {
    if (!fetched && !loading) onFetch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="tkdl">
      <div className="tkdl__banner">
        TKDL Search — DEMONSTRATION DATA. Not connected to the live Traditional Knowledge Digital
        Library.
      </div>

      {loading && <p className="tkdl__status">Checking against the demo TKDL dataset…</p>}
      {error && <p className="tkdl__status tkdl__status--error">{error}</p>}

      {data && (
        <>
          <div className="tkdl__assessment card">
            <span className={`tkdl__risk tkdl__risk--${data.assessment.risk_level}`}>
              {data.assessment.risk_level.toUpperCase()} overlap risk
            </span>

            {data.assessment.closest_record && (
              <p className="tkdl__closest">
                Closest match: <strong>{data.assessment.closest_record.formulation_name}</strong>{' '}
                ({data.assessment.closest_record.record_id}, {data.assessment.closest_record.source_text})
              </p>
            )}

            {data.assessment.reasoning?.length > 0 && (
              <ul className="tkdl__list">
                {data.assessment.reasoning.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            )}

            {data.assessment.what_was_already_known?.length > 0 && (
              <div className="tkdl__section">
                <p className="tkdl__section-title">Already documented</p>
                <ul className="tkdl__list">
                  {data.assessment.what_was_already_known.map((x, i) => (
                    <li key={i}>{x}</li>
                  ))}
                </ul>
              </div>
            )}

            {data.assessment.what_appears_different?.length > 0 && (
              <div className="tkdl__section">
                <p className="tkdl__section-title">Appears different</p>
                <ul className="tkdl__list">
                  {data.assessment.what_appears_different.map((x, i) => (
                    <li key={i}>{x}</li>
                  ))}
                </ul>
              </div>
            )}

            {data.assessment.potential_novel_features?.length > 0 && (
              <div className="tkdl__section">
                <p className="tkdl__section-title">Potential novel features</p>
                <ul className="tkdl__list">
                  {data.assessment.potential_novel_features.map((x, i) => (
                    <li key={i}>{x}</li>
                  ))}
                </ul>
              </div>
            )}

            <p className="tkdl__disclaimer">{data.assessment.disclaimer}</p>
          </div>

          <div className="tkdl__matches">
            <p className="tkdl__matches-title">All candidate records ({data.matches.length})</p>
            {data.matches.length === 0 && (
              <p className="tkdl__status">No matches in the demo dataset for this composition.</p>
            )}
            {data.matches.map((m) => (
              <div key={m.record.record_id} className="tkdl__match card">
                <p className="tkdl__match-name">
                  {m.record.formulation_name}
                  <span className="tkdl__match-id"> — {m.record.record_id}</span>
                </p>
                <p className="tkdl__match-source">{m.record.source_text}</p>
                <p className="tkdl__match-overlap">
                  {Math.round(m.overlap_ratio * 100)}% ingredient overlap
                </p>
                {m.matched_ingredient_names.length > 0 && (
                  <p className="tkdl__match-detail">
                    <strong>Matched:</strong> {m.matched_ingredient_names.join(', ')}
                  </p>
                )}
                {m.unmatched_tkdl_ingredient_names.length > 0 && (
                  <p className="tkdl__match-detail">
                    <strong>In record, not yours:</strong>{' '}
                    {m.unmatched_tkdl_ingredient_names.join(', ')}
                  </p>
                )}
              </div>
            ))}
          </div>

          <button type="button" className="tkdl__refresh" onClick={onFetch} disabled={loading}>
            Re-check
          </button>
        </>
      )}
    </div>
  );
}
