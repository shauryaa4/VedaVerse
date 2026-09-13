import type { Citation } from '../types'
import { VerifiedBadge } from './Badge'

interface CitationModalProps {
  citation: Citation
  onClose: () => void
}

export function CitationModal({ citation, onClose }: CitationModalProps) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <div className="modal-title">{citation.doc_id}</div>
            <div style={{ fontSize: '13px', color: 'var(--c-text-muted)', marginTop: '2px' }}>
              {citation.section}
            </div>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close">&times;</button>
        </div>
        <div className="modal-body">
          <div className="modal-excerpt">{citation.excerpt}</div>
          <VerifiedBadge />
        </div>
      </div>
    </div>
  )
}
