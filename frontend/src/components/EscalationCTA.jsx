import { useState } from 'react';
import EscalationModal from './EscalationModal.jsx';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';
import './EscalationCTA.css';

export default function EscalationCTA({ currentLang = 'en' }) {
  const [modalOpen, setModalOpen] = useState(false);
  const uiText = useTranslatedTexts([
    'This is information, not legal advice.', 'Talk to an IP facilitator',
  ], currentLang);

  return (
    <>
      <div className="escalation-cta" role="complementary">
        <p className="escalation-cta__text">
          {uiText('This is information, not legal advice.')}
        </p>
        <button
          type="button"
          className="escalation-cta__button"
          onClick={() => setModalOpen(true)}
        >
          {uiText('Talk to an IP facilitator')}
        </button>
      </div>

      {modalOpen && <EscalationModal onClose={() => setModalOpen(false)} currentLang={currentLang} />}
    </>
  );
}
