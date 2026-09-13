import { useState } from 'react';
import AnswerCard from './AnswerCard.jsx';
import { OBJECTIVE_OPTIONS, CATEGORY_LABELS } from '../data/options.js';
import './QueryWorkspace.css';

/**
 * FE-06/07/08 — Part 2's Query + Answer workspace.
 *
 * Replaces WorkspacePlaceholder.jsx entirely (deleted in this part, per
 * that file's own docstring: "Part 2 deletes this file entirely rather
 * than editing around it").
 *
 * Per build spec §15 item 5, the query screen is "seeded with objective
 * checkboxes from intake" — rather than literal checkboxes (the objectives
 * were already submitted during the questionnaire), these render as
 * clickable starter-question chips so a judge/user can jump straight to
 * the question the intake flow indicated they cared about, without typing
 * it out.
 *
 * Owns only the question textarea's local input state. Every backend call
 * (askQuestion, getCitation) and the resulting history/modal state lives
 * in App.jsx and arrives here as props — the same split Part 1 established
 * for the wizard screens.
 */
const STARTER_QUESTIONS = {
  patentability: 'Can I patent this formulation?',
  regulatory_category: 'What regulatory category does this product fall under?',
  trademark: 'How can I protect the brand or product name?',
  prior_art: 'Has a formulation like this been done before?',
  abs_relevance: 'Do Access and Benefit-Sharing obligations apply to this product?',
  legal_pathway: 'What is the overall legal pathway for protecting this product?',
  general: 'What should I know about protecting this product?',
};

export default function QueryWorkspace({
  pip,
  classification,
  history,
  onAsk,
  loading,
  error,
  onOpenCitation,
}) {
  const [question, setQuestion] = useState('');
  // Part 3 — Hindi toggle. /query already accepts language: "en"|"hi" and
  // does the actual translation itself (backend/logic/language.py, via
  // Gemini) — there's no separate "translate my question" step here, just
  // this parameter passed through onAsk. Labeled honestly per build spec
  // §12: this is NOT live Bhashini (there's an unmounted, non-functional
  // backend/routes/bhashini_routes.py in the repo that imports a
  // backend/logic/bhashini_mock.py that doesn't exist — dead code, not
  // wired into main.py's routers) — so this is the "translation-assisted"
  // fallback path, said as such in the UI rather than claiming Bhashini.
  const [language, setLanguage] = useState('en');

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || loading) return;
    onAsk(trimmed, language);
    setQuestion('');
  };

  const objectives = pip?.objective || [];
  const categoryLabel = CATEGORY_LABELS[classification?.category] || classification?.category || '—';

  return (
    <div className="workspace">
      <div className="workspace__summary card">
        <dl>
          <div>
            <dt>Jurisdiction</dt>
            <dd>{pip?.jurisdiction === 'india' ? 'India' : pip?.jurisdiction === 'international' ? 'International' : '—'}</dd>
          </div>
          <div>
            <dt>Category</dt>
            <dd>{categoryLabel}</dd>
          </div>
        </dl>
      </div>

      {objectives.length > 0 && (
        <div className="workspace__objectives">
          <p className="workspace__objectives-label">Based on what you told us, you might ask:</p>
          <div className="workspace__objective-chips">
            {objectives.map((obj) => (
              <button
                key={obj}
                type="button"
                className="workspace__objective-chip"
                onClick={() => setQuestion(STARTER_QUESTIONS[obj] || OBJECTIVE_OPTIONS.find((o) => o.value === obj)?.label || obj)}
                disabled={loading}
              >
                {OBJECTIVE_OPTIONS.find((o) => o.value === obj)?.label || obj}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="workspace__language" role="radiogroup" aria-label="Answer language">
        <label className="workspace__language-option">
          <input
            type="radio"
            name="language"
            value="en"
            checked={language === 'en'}
            onChange={() => setLanguage('en')}
            disabled={loading}
          />
          English
        </label>
        <label className="workspace__language-option">
          <input
            type="radio"
            name="language"
            value="hi"
            checked={language === 'hi'}
            onChange={() => setLanguage('hi')}
            disabled={loading}
          />
          हिंदी (Hindi)
        </label>
        {language === 'hi' && (
          <span className="workspace__language-note">
            Hindi support (translation-assisted) — not live Bhashini.
          </span>
        )}
      </div>

      <form className="workspace__form" onSubmit={handleSubmit}>
        <textarea
          className="workspace__input"
          placeholder="Ask a question about this product's IP or regulatory pathway…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={3}
          disabled={loading}
        />
        <button type="submit" className="workspace__submit" disabled={loading || !question.trim()}>
          {loading ? 'Asking…' : 'Ask'}
        </button>
      </form>

      {error && <p className="workspace__error">{error}</p>}

      <div className="workspace__history">
        {history.length === 0 && !loading && (
          <p className="workspace__empty">
            Ask a question above to get a grounded, citation-backed answer.
          </p>
        )}
        {loading && (
          <p className="workspace__loading">Retrieving and verifying an answer…</p>
        )}
        {history
          .slice()
          .reverse()
          .map((turn) => (
            <AnswerCard key={turn.id} turn={turn} onOpenCitation={onOpenCitation} />
          ))}
      </div>
    </div>
  );
}
