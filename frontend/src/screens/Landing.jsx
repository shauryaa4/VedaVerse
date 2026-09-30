import ErrorNotice from '../components/ErrorNotice.jsx';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';
import './Landing.css';

export default function Landing({ onStart, loading, error, currentLang = 'en' }) {
  const uiText = useTranslatedTexts([
    'Know how the law treats your Ayurvedic product — before you file anything.',
    'Formulation-aware classification, not a generic chatbot guess',
    'Every claim traces back to an actual statute, rule, or treaty section',
    'India and international answers are kept in separate, labelled lanes',
    'Try again', 'Starting session…', 'Start Assessment',
    'This tool provides information, not legal advice.', 'IP-SAKTI SAHAYAK',
  ], currentLang);
  return (
    <div className="landing">
      <section className="landing__content">
        <div className="landing__brand">
          <svg className="landing__brand-mark" viewBox="0 0 48 48" aria-hidden="true">
            <path d="M23 8v27M14 15h18M14 15 8 26h12L14 15Zm18 0-6 11h12L32 15ZM18 39h12" />
            <path d="M5 27c2.4 3 5.6 3 8 0m14 0c2.4 3 5.6 3 8 0" />
            <path d="M18 39h12l-2 4h-8z" />
          </svg>
          <strong>{uiText('IP-SAKTI SAHAYAK')}</strong>
        </div>
        <p className="landing__eyebrow">AIIA · Ministry of AYUSH · SIH 26045</p>
        <h1 className="landing__title">
          {uiText('Know how the law treats your Ayurvedic product — before you file anything.')}
        </h1>
        <ul className="landing__points">
          <li>{uiText('Formulation-aware classification, not a generic chatbot guess')}</li>
          <li>{uiText('Every claim traces back to an actual statute, rule, or treaty section')}</li>
          <li>{uiText('India and international answers are kept in separate, labelled lanes')}</li>
        </ul>

        <ErrorNotice error={error} onRetry={onStart} retryLabel={uiText('Try again')} currentLang={currentLang} />

        <button
          type="button"
          className="landing__cta"
          onClick={onStart}
          disabled={loading}
        >
          {loading ? uiText('Starting session…') : uiText('Start Assessment')}
        </button>

        <p className="landing__disclaimer">
          {uiText('This tool provides information, not legal advice.')}
        </p>
      </section>
      <div className="landing__visual" role="img" aria-label="Ayurvedic herbs and ingredients">
        <img src="/ayurvedic-ingredients.jpg" alt="Ayurvedic herbs, roots and ingredients" />
      </div>
    </div>
  );
}
