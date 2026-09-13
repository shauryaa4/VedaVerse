import './AppHeader.css';

const STEPS = [
  { key: 'jurisdiction', label: 'Jurisdiction' },
  { key: 'questionnaire', label: 'Questionnaire' },
  { key: 'classification', label: 'Classification' },
  { key: 'workspace', label: 'Ask & Explore' },
];

export default function AppHeader({ step, jurisdiction, onRestart }) {
  const activeIndex = STEPS.findIndex((s) => s.key === step);

  return (
    <header className="app-header">
      <div className="app-header__top">
        <button className="app-header__brand" onClick={onRestart} type="button">
          <span className="app-header__brand-mark">IP</span>
          <span className="app-header__brand-text">
            <span className="app-header__brand-title">IP-SAKTI Sahayak</span>
            <span className="app-header__brand-subtitle">AYUSH IP &amp; regulatory guidance</span>
          </span>
        </button>

        {jurisdiction && (
          <span className={`app-header__jurisdiction app-header__jurisdiction--${jurisdiction}`}>
            {jurisdiction === 'india' ? 'India' : 'International'}
          </span>
        )}
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
              <span className="app-header__step-label">{s.label}</span>
            </li>
          ))}
        </ol>
      )}
    </header>
  );
}
