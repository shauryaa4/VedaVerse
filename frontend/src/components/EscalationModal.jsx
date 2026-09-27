import useTranslatedTexts from '../utils/useTranslatedTexts.js';
import './EscalationModal.css';

export default function EscalationModal({ onClose, currentLang = 'en' }) {
  const uiText = useTranslatedTexts([
    'Connect with an IP facilitator',
    "IP-SAKTI Sahayak gives you information to help you understand your options — it doesn't replace a registered IP facilitator or patent agent. For guidance specific to your situation, reach out directly.",
    'Email an IP facilitator', 'Close',
  ], currentLang);
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
          {uiText('Connect with an IP facilitator')}
        </h2>
        <p className="escalation-modal__body">
          {uiText("IP-SAKTI Sahayak gives you information to help you understand your options — it doesn't replace a registered IP facilitator or patent agent. For guidance specific to your situation, reach out directly.")}
        </p>
        <a
          className="escalation-modal__link"
          href="mailto:facilitator@example.org?subject=IP%20guidance%20request"
        >
          {uiText('Email an IP facilitator')}
        </a>
        <button
          type="button"
          className="escalation-modal__close"
          onClick={onClose}
        >
          {uiText('Close')}
        </button>
      </div>
    </div>
  );
}
