import { useState } from 'react';
import EscalationModal from './EscalationModal.jsx';
import './EscalationCTA.css';

/**
 * FE-09 — Escalation CTA.
 *
 * Per build spec section 15 (item 10), this is PERSISTENT — it must appear on
 * every answer screen, not just the abstain state. Per N-D5-04, it sits
 * alongside (not instead of) the confidence badge; this component owns only
 * the disclaimer + escalation action, nothing about confidence state.
 *
 * No backend endpoint exists yet for a real facilitator handoff, so this
 * opens a lightweight stub modal (per the feasibility doc's own suggestion:
 * "can literally be a contact-form stub"). Swap EscalationModal's contents
 * for a real form/booking flow later without changing this component's API.
 */
export default function EscalationCTA() {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <>
      <div className="escalation-cta" role="complementary">
        <p className="escalation-cta__text">
          This is information, not legal advice.
        </p>
        <button
          type="button"
          className="escalation-cta__button"
          onClick={() => setModalOpen(true)}
        >
          Talk to an IP facilitator
        </button>
      </div>

      {modalOpen && <EscalationModal onClose={() => setModalOpen(false)} />}
    </>
  );
}
