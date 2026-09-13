import ConfidenceBadge from '../components/ConfidenceBadge.jsx';
import { parseCitationMarkers } from '../utils/parseCitations.js';
import './AnswerCard.css';

/**
 * FE-07/08. Renders one turn of the workspace's Q&A history — the question
 * as asked, then exactly what POST /query returned for it.
 *
 * Renders answer_text and abstain_reason verbatim, never paraphrased —
 * per build spec §9, the abstention message must never pass through any
 * paraphrasing layer, and per §4/CLS, the same "don't re-derive it"
 * principle applies to everything the backend already decided.
 *
 * Inline [doc_id:section] markers become clickable citation chips via
 * parseCitationMarkers — clicking one opens the citation detail modal
 * (owned by App.jsx, wired through the onOpenCitation prop).
 */
export default function AnswerCard({ turn, onOpenCitation }) {
  const { question, result, language } = turn;
  const {
    answer_text: answerText,
    abstained,
    abstain_reason: abstainReason,
    confidence,
    status_notes: statusNotes,
  } = result;

  const parts = abstained ? [] : parseCitationMarkers(answerText);

  return (
    <div className="answer-card card">
      <p className="answer-card__question">
        {question}
        {language === 'hi' && <span className="answer-card__lang-tag">हिंदी</span>}
      </p>

      <div className="answer-card__meta">
        <ConfidenceBadge confidence={confidence} abstained={abstained} />
      </div>

      {abstained ? (
        <div className="answer-card__abstain">
          <p className="answer-card__abstain-text">
            {abstainReason ||
              'Insufficient authoritative evidence in our corpus to answer this reliably. This may be outside the scope of our current legal database, or the question may require case-specific analysis. We recommend consulting a registered IP facilitator or patent agent for this query.'}
          </p>
        </div>
      ) : (
        <p className="answer-card__text">
          {parts.map((part, i) =>
            typeof part === 'string' ? (
              <span key={i}>{part}</span>
            ) : (
              <button
                key={i}
                type="button"
                className="answer-card__citation-chip"
                onClick={() => onOpenCitation(part.docId, part.section, part.label)}
              >
                {part.label}
              </button>
            )
          )}
        </p>
      )}

      {statusNotes?.length > 0 && (
        <div className="answer-card__notes">
          {statusNotes.map((note, i) => (
            <p key={i} className="answer-card__note">
              ⚠ {note}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
