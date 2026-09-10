import './EscalationModal.css';

/**
 * Stub escalation modal. Per the feasibility doc's own guidance, a real
 * facilitator-matching backend is out of scope for the hackathon — this is
 * intentionally a contact-form stub, not a broken promise of live routing.
 * Replace the mailto link with a real form/booking flow if that ever exists.
 */
export default function EscalationModal({ onClose }) {
  return (
    <div className="escalation-modal__overlay" onClick={onClose}>
      <div
        className="escalation-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="escalation-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="escalation-modal-title" className="escalation-modal__title">
          Connect with an IP facilitator
        </h2>
        <p className="escalation-modal__body">
          IP-SAKTI Sahayak gives you information to help you understand your
          options — it doesn't replace a registered IP facilitator or patent
          agent. For guidance specific to your situation, reach out directly.
        </p>
        <a
          className="escalation-modal__link"
          href="mailto:facilitator@example.org?subject=IP%20guidance%20request"
        >
          Email an IP facilitator
        </a>
        <button
          type="button"
          className="escalation-modal__close"
          onClick={onClose}
        >
          Close
        </button>
      </div>
    </div>
  );
}
