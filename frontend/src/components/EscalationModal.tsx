interface EscalationModalProps {
  onClose: () => void
}

export function EscalationModal({ onClose }: EscalationModalProps) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">Talk to an IP Facilitator</div>
          <button className="modal-close" onClick={onClose} aria-label="Close">&times;</button>
        </div>
        <div className="modal-body">
          <p style={{ fontSize: '15px', color: 'var(--c-text-secondary)', lineHeight: 1.7, marginBottom: '20px' }}>
            For case-specific legal analysis, we recommend consulting a registered IP
            facilitator or patent agent. They can provide tailored guidance on your
            product's patentability, regulatory pathway, and compliance requirements.
          </p>
          <div className="note-box" style={{ marginBottom: '20px' }}>
            <span className="note-icon">i</span>
            <span>This is a prototype. In the full version, this action will connect you to a verified IP facilitator from the registered directory.</span>
          </div>
          <button className="btn btn-primary" onClick={onClose}>Got it</button>
        </div>
      </div>
    </div>
  )
}
