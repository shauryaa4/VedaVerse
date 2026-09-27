import { useState } from 'react';
import { SUPPORTED_LANGUAGES } from '../utils/translator.js';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';
import './WorkspaceSidebar.css';

export default function WorkspaceSidebar({ active, signedIn = false, user, onDashboard, onHistory, onLogout, language = 'en', onLanguageChange }) {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [productsOpen, setProductsOpen] = useState(false);
  const [comingSoonOpen, setComingSoonOpen] = useState('');
  const uiText = useTranslatedTexts(['WORKSPACE', 'Dashboard', 'MY PRODUCTS', 'Product tracking is coming soon.', 'Case History', 'Language:', 'Language', 'Settings', 'More account settings are coming soon.', 'Sign Out', 'Guest session', 'Connect to IP Facilitator', 'Legal Journey Assistance', 'COMING SOON', 'Request a human IP facilitator to review your case and guide next steps.', 'Build a document checklist and action plan from your products and case history.'], language);
  const currentLanguage = SUPPORTED_LANGUAGES.find((item) => item.code === language);

  return (
    <aside className="workspace-sidebar" aria-label="Workspace navigation">
      <div className="workspace-sidebar__section-label">{uiText('WORKSPACE')}</div>
      <nav className="workspace-sidebar__nav" aria-label="Workspace">
        <button type="button" onClick={onDashboard} className={`workspace-sidebar__link${active === 'dashboard' ? ' is-active' : ''}`}>
          <span className="workspace-sidebar__icon" aria-hidden="true">⌂</span><span>{uiText('Dashboard')}</span>
        </button>
        <button type="button" onClick={() => setProductsOpen((open) => !open)} className="workspace-sidebar__link" aria-expanded={productsOpen}>
          <span className="workspace-sidebar__icon" aria-hidden="true">▱</span><span>{uiText('MY PRODUCTS')}</span>
        </button>
        {productsOpen && <p className="workspace-sidebar__settings-note">{uiText('Product tracking is coming soon.')}</p>}
        <button type="button" onClick={onHistory} className={`workspace-sidebar__link${active === 'history' ? ' is-active' : ''}`}>
          <span className="workspace-sidebar__icon" aria-hidden="true">◴</span><span>{uiText('Case History')}</span>
        </button>
        <button type="button" onClick={() => setComingSoonOpen((open) => open === 'facilitator' ? '' : 'facilitator')} className="workspace-sidebar__link workspace-sidebar__future-link" aria-expanded={comingSoonOpen === 'facilitator'}>
          <span className="workspace-sidebar__icon" aria-hidden="true">♧</span><span>{uiText('Connect to IP Facilitator')}<small>{uiText('COMING SOON')}</small></span>
        </button>
        {comingSoonOpen === 'facilitator' && <p className="workspace-sidebar__settings-note">{uiText('Request a human IP facilitator to review your case and guide next steps.')}</p>}
        <button type="button" onClick={() => setComingSoonOpen((open) => open === 'journey' ? '' : 'journey')} className="workspace-sidebar__link workspace-sidebar__future-link" aria-expanded={comingSoonOpen === 'journey'}>
          <span className="workspace-sidebar__icon" aria-hidden="true">⌁</span><span>{uiText('Legal Journey Assistance')}<small>{uiText('COMING SOON')}</small></span>
        </button>
        {comingSoonOpen === 'journey' && <p className="workspace-sidebar__settings-note">{uiText('Build a document checklist and action plan from your products and case history.')}</p>}
      </nav>

      <div className="workspace-sidebar__bottom">
        <label className="workspace-sidebar__language">
          <span className="workspace-sidebar__icon" aria-hidden="true">◎</span>
          <span>{uiText('Language:')}</span>
          <select value={language} onChange={(event) => onLanguageChange?.(event.target.value)} aria-label={uiText('Language')}>
            {SUPPORTED_LANGUAGES.map((item) => <option key={item.code} value={item.code}>{item.native}</option>)}
          </select>
          <span className="workspace-sidebar__language-name">{currentLanguage?.native || 'English'}</span>
          <span className="workspace-sidebar__chevron" aria-hidden="true">⌄</span>
        </label>
        <button type="button" className="workspace-sidebar__utility" onClick={() => setSettingsOpen((open) => !open)} aria-expanded={settingsOpen}>
          <span className="workspace-sidebar__icon" aria-hidden="true">⚙</span><span>{uiText('Settings')}</span>
        </button>
        {settingsOpen && <p className="workspace-sidebar__settings-note">{uiText('More account settings are coming soon.')}</p>}
        {signedIn && <button type="button" className="workspace-sidebar__utility workspace-sidebar__signout" onClick={onLogout}>
          <span className="workspace-sidebar__icon" aria-hidden="true">⇥</span><span>{uiText('Sign Out')}</span>
        </button>}
        {!signedIn && <div className="workspace-sidebar__guest-label"><span className="workspace-sidebar__icon" aria-hidden="true">◉</span><span>{uiText('Guest session')}</span></div>}
      </div>
    </aside>
  );
}
