import ErrorNotice from '../components/ErrorNotice.jsx';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';
import { SUPPORTED_LANGUAGES } from '../utils/translator.js';
import './Landing.css';

export default function Landing({ onStart, loading, error, currentLang = 'en', onLanguageChange }) {
  const uiText = useTranslatedTexts([
    'Language',
    'Know how the law treats your Ayurvedic product — before you file anything.',
    'Classical formulation or new combination? India or international? Patent, trademark, or regulatory pathway? Answer a few questions and get a grounded, citation-backed answer — with a confidence score, and an honest "we don\'t know" when the corpus doesn\'t cover it.',
    'Formulation-aware classification, not a generic chatbot guess',
    'Every claim traces back to an actual statute, rule, or treaty section',
    'India and international answers are kept in separate, labelled lanes',
    'Try again', 'Starting session…', 'Start Assessment',
    'This tool provides information, not legal advice.',
  ], currentLang);
  return (
    <div className="landing">
      <div className="landing__card card">
        <label className="landing__language"><span>{uiText('Language')}</span><select aria-label={uiText('Language')} value={currentLang} onChange={(event) => onLanguageChange?.(event.target.value)}>{SUPPORTED_LANGUAGES.map((language) => <option key={language.code} value={language.code}>{language.native}</option>)}</select></label>
        <p className="landing__eyebrow">AIIA · Ministry of AYUSH · SIH 26045</p>
        <h1 className="landing__title">
          {uiText('Know how the law treats your Ayurvedic product — before you file anything.')}
        </h1>
        <p className="landing__body">
          {uiText('Classical formulation or new combination? India or international? Patent, trademark, or regulatory pathway? Answer a few questions and get a grounded, citation-backed answer — with a confidence score, and an honest "we don\'t know" when the corpus doesn\'t cover it.')}
        </p>

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
      </div>
    </div>
  );
}
