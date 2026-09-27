import { SUPPORTED_LANGUAGES } from '../utils/translator.js';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';
import './AppHeader.css';

const STEPS = [
  { key: 'jurisdiction', label: 'Jurisdiction' },
  { key: 'questionnaire', label: 'Questionnaire' },
  { key: 'classification', label: 'Classification' },
  { key: 'workspace', label: 'Ask & Explore' },
];

export default function AppHeader({
  step,
  jurisdiction,
  language = 'en',
  onLanguageChange,
  onRestart,
}) {
  const activeIndex = STEPS.findIndex((s) => s.key === step);
  const uiText = useTranslatedTexts([
    'AYUSH IP & regulatory guidance', 'India', 'International', 'Select Site Language',
    ...STEPS.map((item) => item.label),
  ], language);

  return (
    <header className="app-header">
      <div className="app-header__top">
        <button className="app-header__brand" onClick={onRestart} type="button">
          <span className="app-header__brand-mark">IP</span>
          <span className="app-header__brand-text">
            <span className="app-header__brand-title">IP-SAKTI Sahayak</span>
            <span className="app-header__brand-subtitle">{uiText('AYUSH IP & regulatory guidance')}</span>
          </span>
        </button>

        <div className="app-header__actions">
          {jurisdiction && (
            <span className={`app-header__jurisdiction app-header__jurisdiction--${jurisdiction}`}>
              {jurisdiction === 'india' ? uiText('India') : uiText('International')}
            </span>
          )}

          <div className="app-header__lang-picker">
            <span className="app-header__lang-icon" aria-hidden="true">🌐</span>
            <select
              className="app-header__lang-select"
              value={language}
              onChange={(e) => onLanguageChange && onLanguageChange(e.target.value)}
              title={uiText('Select Site Language')}
              aria-label={uiText('Select Site Language')}
            >
              {SUPPORTED_LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.native} ({l.label})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {activeIndex >= 0 && (
        <ol className="app-header__steps">
          {STEPS.map((s, i) => (
            <li
              key={s.key}
              className={
                'app-header__step' +
                (i === activeIndex ? ' app-header__step--active' : '') +
                (i < activeIndex ? ' app-header__step--done' : '')
              }
            >
              <span className="app-header__step-index">{i + 1}</span>
              <span className="app-header__step-label">{uiText(s.label)}</span>
            </li>
          ))}
        </ol>
      )}
    </header>
  );
}
