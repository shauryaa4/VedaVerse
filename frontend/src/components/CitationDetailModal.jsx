import './CitationDetailModal.css';

/**
 * N-D5-03 — citation detail modal, one of the three "never cut" USPs
 * (build spec §20). Fetching happens in App.jsx via GET
 * /citation/{doc_id}/{section} (api/client.js's getCitation) — this
 * component is pure presentation over whatever state App.jsx hands it,
 * matching the split Part 1 established (screens/components never call
 * api/client.js directly).
 *
 * Per N-D5-03's "degrade gracefully" acceptance criterion: if the fetch
 * fails (e.g. citation not found, or /query hasn't populated the cache
 * for this session), this still shows the citation label and the error,
 * rather than leaving a blank modal.
 */
export default function CitationDetailModal({ label, loading, error, detail, onClose }) {
  return (
    <div className="citation-modal__overlay" onClick={onClose}>
      <div
        className="citation-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="citation-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <p className="citation-modal__eyebrow">Citation</p>
        <h2 id="citation-modal-title" className="citation-modal__title">
          {label}
        </h2>

        {loading && <p className="citation-modal__status">Loading source text…</p>}
        {error && <p className="citation-modal__status citation-modal__status--error">{error}</p>}

        {detail && (
          <>
            <p className="citation-modal__doc">
              {detail.doc_name}
              {detail.section ? ` — ${detail.section}` : ''}
            </p>
            <span
              className={
                'citation-modal__badge ' +
                (detail.verified
                  ? 'citation-modal__badge--verified'
                  : 'citation-modal__badge--unverified')
              }
            >
              {detail.verified ? 'Verified \u2713' : 'Not fully supported'}
            </span>
            <blockquote className="citation-modal__excerpt">{detail.excerpt_text}</blockquote>
          </>
        )}

        <button type="button" className="citation-modal__close" onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  );
}
