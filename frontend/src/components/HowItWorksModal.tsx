interface HowItWorksModalProps {
  onClose: () => void
}

export function HowItWorksModal({ onClose }: HowItWorksModalProps) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-title">How this works</div>
          <button className="modal-close" onClick={onClose} aria-label="Close">&times;</button>
        </div>
        <div className="modal-body">
          <p style={{ fontSize: '15px', color: 'var(--c-text-secondary)', lineHeight: 1.7, marginBottom: '20px' }}>
            IP-SAKTI Sahayak guides Ayurveda product makers through the IP and regulatory
            landscape in five stages:
          </p>
          <ol className="how-it-works-list">
            <li>
              <span className="hiw-step">1</span>
              <div>
                <div className="hiw-title">Classify</div>
                <div className="hiw-desc">Answer a short questionnaire about your product. A deterministic rule engine maps your answers to one of six IP/regulatory categories.</div>
              </div>
            </li>
            <li>
              <span className="hiw-step">2</span>
              <div>
                <div className="hiw-title">Route</div>
                <div className="hiw-desc">Based on the classification, the tool identifies which legal frameworks apply — patent law, drug regulation, food law, or biodiversity law.</div>
              </div>
            </li>
            <li>
              <span className="hiw-step">3</span>
              <div>
                <div className="hiw-title">Retrieve</div>
                <div className="hiw-desc">When you ask a question, the system retrieves relevant legal provisions and source documents from its corpus.</div>
              </div>
            </li>
            <li>
              <span className="hiw-step">4</span>
              <div>
                <div className="hiw-title">Verify</div>
                <div className="hiw-desc">Each answer includes inline citations to the exact statute and section. You can click any citation to see the source excerpt and a verification badge.</div>
              </div>
            </li>
            <li>
              <span className="hiw-step">5</span>
              <div>
                <div className="hiw-title">Answer or Abstain</div>
                <div className="hiw-desc">If the corpus has sufficient authoritative evidence, you get a grounded answer. If not, the system abstains and recommends consulting a registered IP facilitator.</div>
              </div>
            </li>
          </ol>
          <div className="note-box" style={{ marginTop: '20px' }}>
            <span className="note-icon">i</span>
            <span>This is a prototype. The classification engine is deterministic; the question-answering uses mock data that will be replaced with real retrieval.</span>
          </div>
        </div>
      </div>
    </div>
  )
}
