import './WorkspacePlaceholder.css';

/**
 * TEMPORARY — replaced in Part 2 (Query/Answer screens, wired to /query and
 * the citation endpoint) and Part 3 (TKDL Search + ABS Helper tabs). Kept
 * deliberately thin so there's nothing here to unwind later: Part 2 deletes
 * this file entirely rather than editing around it.
 */
export default function WorkspacePlaceholder({ pip, classification, onBack }) {
  return (
    <div className="workspace-placeholder">
      <div className="workspace-placeholder__card card">
        <p className="workspace-placeholder__eyebrow">Coming in Part 2</p>
        <h2>Ask a question</h2>
        <p className="workspace-placeholder__body">
          The Query and Answer screens (wired to <code>/query</code>, with citations,
          confidence badge, and safe abstention) land in the next part. Your session and
          classification are saved on the backend, so nothing here needs to be redone.
        </p>

        <dl className="workspace-placeholder__summary">
          <div>
            <dt>Session</dt>
            <dd>{pip?.session_id || '—'}</dd>
          </div>
          <div>
            <dt>Jurisdiction</dt>
            <dd>{pip?.jurisdiction || '—'}</dd>
          </div>
          <div>
            <dt>Category</dt>
            <dd>{classification?.category || '—'}</dd>
          </div>
          <div>
            <dt>Objectives</dt>
            <dd>{pip?.objective?.join(', ') || '—'}</dd>
          </div>
        </dl>

        <button type="button" className="workspace-placeholder__back" onClick={onBack}>
          Back to classification
        </button>
      </div>
    </div>
  );
}
