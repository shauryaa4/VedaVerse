import useTranslatedTexts from '../utils/useTranslatedTexts.js';
import { SUPPORTED_LANGUAGES } from '../utils/translator.js';
import './AppHeader.css';

const STEPS = [
  { key: 'jurisdiction', label: 'Jurisdiction' },
  { key: 'questionnaire', label: 'Questionnaire' },
  { key: 'classification', label: 'Classification' },
  { key: 'workspace', label: 'Ask & Explore' },
];

const KHUSHI_VERMA = {
  hi: 'ख़ुशी वर्मा', ta: 'குஷி வர்மா', bn: 'খুশি ভার্মা', te: 'ఖుషి వర్మ',
  mr: 'ख़ुशी वर्मा', gu: 'ખુશી વર્મા', kn: 'ಖುಷಿ ವರ್ಮಾ', ml: 'ഖുഷി വർമ്മ',
  pa: 'ਖੁਸ਼ੀ ਵਰਮਾ', or: 'ଖୁସି ବର୍ମା', ur: 'خوشی ورما',
};

export default function AppHeader({
  step,
  language = 'en',
  onRestart,
  onAccountAction,
  user,
  showDashboard = false,
  onDashboard,
  onStepSelect,
  onLanguageChange,
}) {
  const isLanding = step === 'landing';
  const activeIndex = STEPS.findIndex((s) => s.key === step);
  const profileNameKey = user?.name?.trim().replace(/\s+/g, ' ').toLocaleLowerCase();
  const localizedProfileName = profileNameKey === 'khushi verma' ? (KHUSHI_VERMA[language] || user.name) : user?.name;
  const uiText = useTranslatedTexts([
    'IP-SAKTI Sahayak', 'AYUSH IP & regulatory guidance', 'India', 'International',
    'Dashboard', 'Language',
    'Log in', 'Sign up', ...STEPS.map((item) => item.label),
  ], language);

  return (
    <header className={`app-header${isLanding ? ' app-header--landing' : ''}`}>
      <div className="app-header__top">
        {!isLanding && <button className="app-header__brand" onClick={onRestart} type="button">
          <span className="app-header__brand-mark">IP</span>
          <span className="app-header__brand-text">
            <span className="app-header__brand-title">{uiText('IP-SAKTI Sahayak')}</span>
            <span className="app-header__brand-subtitle">{uiText('AYUSH IP & regulatory guidance')}</span>
          </span>
        </button>}

        {isLanding && <label className="app-header__landing-language">
          <span>{uiText('Language')}</span>
          <select value={language} onChange={(event) => onLanguageChange?.(event.target.value)} aria-label="Change language">
            {SUPPORTED_LANGUAGES.map((item) => <option key={item.code} value={item.code}>{item.native}</option>)}
          </select>
        </label>}

        <div className="app-header__actions">
          {step && !isLanding && <label className="app-header__language-picker" aria-label="Language">
            <span aria-hidden="true">◎</span>
            <select value={language} onChange={(event) => onLanguageChange?.(event.target.value)} aria-label="Change language">
              {SUPPORTED_LANGUAGES.map((item) => <option key={item.code} value={item.code}>{item.native}</option>)}
            </select>
          </label>}
          {(!step || isLanding) && !user && <div className="app-header__account-actions">
            <button type="button" className="app-header__login" onClick={() => onAccountAction?.('login')}>{uiText('Log in')}</button>
            <button type="button" className="app-header__signup" onClick={() => onAccountAction?.('signup')}>{uiText('Sign up')}</button>
          </div>}
          {showDashboard && <button type="button" className="app-header__dashboard" onClick={onDashboard}><span aria-hidden="true">⌂</span> {uiText('Dashboard')}</button>}
          {user && <div className="app-header__profile"><span className="app-header__profile-avatar">{localizedProfileName?.[0] || 'U'}</span><span className="app-header__profile-name">{localizedProfileName}</span></div>}
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
              <button type="button" className="app-header__step-button" onClick={() => onStepSelect?.(s.key)} aria-current={i === activeIndex ? 'step' : undefined}>
                <span className="app-header__step-index">{i + 1}</span>
                <span className="app-header__step-label">{uiText(s.label)}</span>
              </button>
            </li>
          ))}
        </ol>
      )}
    </header>
  );
}
