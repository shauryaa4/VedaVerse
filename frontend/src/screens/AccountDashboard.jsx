import { useState } from 'react';
import { deleteSavedCase, getSavedCaseDetails } from '../api/client.js';
import './AccountDashboard.css';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';

const LOCALES = { en: 'en-IN', hi: 'hi-IN', ta: 'ta-IN', bn: 'bn-IN', te: 'te-IN', mr: 'mr-IN', gu: 'gu-IN', kn: 'kn-IN', ml: 'ml-IN', pa: 'pa-IN', or: 'or-IN', ur: 'ur-IN' };

function dateLabel(value, language = 'en') {
  if (!value) return 'Just now';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Recently updated' : date.toLocaleString(LOCALES[language] || 'en-IN', { dateStyle: 'medium', timeStyle: 'short' });
}

function HeroArtwork() {
  return (
    <svg className="account-dashboard__art" viewBox="0 0 430 230" role="img" aria-label="Scales of justice resting on books">
      <path d="M334 22c40 20 66 60 66 111v97H250c8-48 17-101 34-142 11-27 27-50 50-66Z" fill="#e0eee3" />
      <path d="M350 49v165m-34-128h69m-68 0-25 48h49l-24-48Zm24 0 25 48h49l-24-48Z" fill="none" stroke="#547861" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M341 48h20m-10-15v17m-51 47c8 10 20 10 28 0m24 0c8 10 20 10 28 0" fill="none" stroke="#6e9276" strokeWidth="4" strokeLinecap="round" />
      <path d="M268 200h143m-129-21h115v20H282z" fill="#245638" />
      <path d="M279 157h119v23H279z" fill="#94b49b" />
      <path d="M270 136h123v20H270z" fill="#3e7952" />
      <text x="291" y="151" fill="#fff" fontSize="10" fontFamily="Georgia,serif" letterSpacing="1.4">INTELLECT</text>
      <text x="300" y="174" fill="#264d34" fontSize="10" fontFamily="Georgia,serif" letterSpacing="1.3">PROPERTY</text>
      <path d="M73 205c4-47 18-88 42-121m-41 119c-21-26-26-50-14-74 18 11 24 35 14 74Zm11-37c-4-30 4-52 28-67 8 23-2 46-28 67Zm11-34c5-24 19-39 44-43 0 23-14 39-44 43Z" fill="#8caf9a" stroke="#628a74" strokeWidth="2" />
      <path d="M53 207h78" stroke="#6c8c7f" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

function ActivityEmpty() {
  return (
    <div className="account-dashboard__activity-empty">
      <div className="account-dashboard__activity-illustration" aria-hidden="true"><span /><i /><b>☰</b></div>
      <strong>No recent updates</strong>
      <p>Your case updates and activity<br />will appear here.</p>
    </div>
  );
}

export default function AccountDashboard({ user, cases, activeCase, activity, loading, startingCase = false, error, onOpenCase, onNewCase, onRefresh, onNavigate, view = 'dashboard', onShowHistory, onBackDashboard, currentLang = 'en' }) {
  const firstName = user?.name?.trim().split(/\s+/)[0] || 'there';
  const hindiKhushi = currentLang === 'hi' && firstName.toLocaleLowerCase() === 'khushi';
  const uiText = useTranslatedTexts(['YOUR IP-SAKTI WORKSPACE', 'Case History', 'Review and continue your saved assessments.', 'Dashboard', 'Loading your cases…', 'Untitled product assessment', 'Classification pending', 'Open case', 'Continue case', 'Unfinished', 'No unfinished case', 'Start a new case to begin an assessment.', 'No saved cases yet', 'Start a case and it will appear in your history.', '＋ Start a New Case', 'Good morning,', 'there', ...(hindiKhushi ? [] : [firstName]), 'Your legal support workspace', 'Opening your case…', 'Continue where you left off', 'Pick up a case or start a new assessment.', 'View all cases', 'Updated', 'In progress', 'No cases yet', 'Your saved assessments will show up here.', 'Explore legal resources', 'Access curated tools and databases to support your legal journey.', 'ABS DATA', 'Explore a wide range of IP-related products and information.', 'Search Legal Corpus', 'Find relevant laws, rules and legal resources in one place.', 'Search TKDL Records', 'Access traditional knowledge digital library records.', 'Your saved case details are stored in this prototype’s account database.', 'Your activity', 'No recent updates', 'Your case updates and activity will appear here.', 'Assistant abstained', 'Response returned', 'Just now', 'Recently updated'], currentLang);
  const latestCase = activeCase;
  const recentActivity = activity?.recent || [];

  if (view === 'history') {
    return (
      <section className="account-dashboard account-dashboard--history">
        <div className="account-dashboard__history-heading"><div><p className="account-dashboard__eyebrow">{uiText('YOUR IP-SAKTI WORKSPACE')}</p><h1>{uiText('Case History')}</h1><p>{uiText('Review and continue your saved assessments.')}</p></div><button type="button" onClick={onBackDashboard}>← {uiText('Dashboard')}</button></div>
        {error && <p className="account-dashboard__error" role="alert">{error.message || error}</p>}
        {loading ? <p className="account-dashboard__case-placeholder">{uiText('Loading your cases…')}</p> : cases.length ? <div className="account-dashboard__history-list">{cases.map((item) => <HistoryCase key={item.session_id} item={item} uiText={uiText} currentLang={currentLang} onOpenCase={onOpenCase} onDelete={onRefresh} />)}</div> : <div className="account-dashboard__history-empty"><h2>{uiText('No saved cases yet')}</h2><p>{uiText('Start a case and it will appear in your history.')}</p><button type="button" className="account-dashboard__primary" onClick={onNewCase}>{uiText('＋ Start a New Case')}</button></div>}
      </section>
    );
  }

  return (
    <section className="account-dashboard">
      <div className="account-dashboard__hero">
        <div className="account-dashboard__hero-copy">
          <p className="account-dashboard__eyebrow">{uiText('YOUR IP-SAKTI WORKSPACE')}</p>
          <h1>{uiText('Good morning,')} {hindiKhushi ? 'ख़ुशी' : uiText(firstName)}</h1>
          <p>{uiText('Your legal support workspace')}</p>
          <button type="button" className="account-dashboard__primary" onClick={onNewCase} disabled={startingCase}>{startingCase ? uiText('Opening your case…') : uiText('＋ Start a New Case')}</button>
        </div>
        <HeroArtwork />
        <div className="account-dashboard__hero-note"><strong>Knowledge<br />for a fairer tomorrow</strong><span /></div>
      </div>

      {error && <p className="account-dashboard__error" role="alert">{error.message || error}</p>}

      <div className="account-dashboard__content-grid">
        <div className="account-dashboard__main-column">
          <section className="account-dashboard__section">
            <div className="account-dashboard__section-heading"><div><h2>{uiText('Continue where you left off')}</h2><p>{uiText('Pick up a case or start a new assessment.')}</p></div><button type="button" onClick={onShowHistory}>{uiText('View all cases')}&nbsp; →</button></div>
            {loading ? <div className="account-dashboard__case-placeholder">{uiText('Loading your cases…')}</div> : latestCase ? (
              <article className="account-dashboard__case-card">
                <span className="account-dashboard__case-icon" aria-hidden="true">▤</span>
                <div className="account-dashboard__case-info"><h3>{latestCase.product_name || uiText('Untitled product assessment')}</h3><p>{uiText('Updated')} {dateLabel(latestCase.updated_at, currentLang)} · {uiText('Unfinished')}</p></div>
                <span className="account-dashboard__case-status">{uiText('In progress')}</span>
                <button type="button" className="account-dashboard__open-case" onClick={() => onOpenCase(latestCase.session_id)}>{uiText('Continue case')}&nbsp; →</button>
              </article>
            ) : (
              <article className="account-dashboard__case-card account-dashboard__case-card--empty">
                <span className="account-dashboard__case-icon" aria-hidden="true">▤</span>
                <div className="account-dashboard__case-info"><h3>{uiText('No unfinished case')}</h3><p>{uiText('Start a new case to begin an assessment.')}</p></div>
                <button type="button" className="account-dashboard__open-case" onClick={onNewCase}>{uiText('＋ Start a New Case')}&nbsp; →</button>
              </article>
            )}
          </section>

          <section className="account-dashboard__section account-dashboard__resources">
            <div className="account-dashboard__section-heading account-dashboard__section-heading--stacked"><div><h2>{uiText('Explore legal resources')}</h2><p>{uiText('Access curated tools and databases to support your legal journey.')}</p></div></div>
            <div className="account-dashboard__resource-grid">
              <button type="button" className="account-dashboard__resource-card" onClick={() => onNavigate('dataset-nba')}><span className="account-dashboard__resource-icon is-gold">◇</span><strong>{uiText('ABS DATA')}</strong><small>{uiText('Explore a wide range of IP-related products and information.')}</small><b aria-hidden="true">→</b></button>
              <button type="button" className="account-dashboard__resource-card" onClick={() => onNavigate('dataset-legal')}><span className="account-dashboard__resource-icon is-blue">⌕</span><strong>{uiText('Search Legal Corpus')}</strong><small>{uiText('Find relevant laws, rules and legal resources in one place.')}</small><b aria-hidden="true">→</b></button>
              <button type="button" className="account-dashboard__resource-card" onClick={() => onNavigate('dataset-tkdl')}><span className="account-dashboard__resource-icon is-green">▤</span><strong>{uiText('Search TKDL Records')}</strong><small>{uiText('Access traditional knowledge digital library records.')}</small><b aria-hidden="true">→</b></button>
            </div>
          </section>
          <p className="account-dashboard__privacy">{uiText('Your saved case details are stored in this prototype’s account database.')}</p>
        </div>

        <aside className="account-dashboard__activity-panel">
          <h2>{uiText('Your activity')}</h2>
          {recentActivity.length === 0 ? <div className="account-dashboard__activity-empty"><div className="account-dashboard__activity-illustration" aria-hidden="true"><span /><i /><b>☰</b></div><strong>{uiText('No recent updates')}</strong><p>{uiText('Your case updates and activity will appear here.')}</p></div> : <div className="account-dashboard__activity-list">{recentActivity.slice(0, 5).map((item, index) => <article key={`${item.session_id}-${item.timestamp}-${index}`}><span className={`account-dashboard__activity-dot${item.abstained ? ' is-abstained' : ''}`}>{item.abstained ? '!' : '✓'}</span><div><p>{item.question}</p><small>{dateLabel(item.timestamp, currentLang)} · {uiText(item.abstained ? 'Assistant abstained' : 'Response returned')}</small></div></article>)}</div>}
        </aside>
      </div>
    </section>
  );
}

function HistoryCase({ item, uiText, currentLang, onOpenCase, onDelete }) {
  const [details, setDetails] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [detailError, setDetailError] = useState('');
  const toggleDetails = async () => {
    if (details) { setDetails(null); return; }
    setLoadingDetails(true); setDetailError('');
    try { setDetails(await getSavedCaseDetails(item.session_id)); }
    catch (error) { setDetailError(error.message || 'Could not load case details.'); }
    finally { setLoadingDetails(false); }
  };
  const removeCase = async () => {
    if (!window.confirm('Delete this completed case and its saved question history? This cannot be undone.')) return;
    try { await deleteSavedCase(item.session_id); await onDelete?.(); }
    catch (error) { setDetailError(error.message || 'Could not delete this case.'); }
  };
  const profile = details?.profile;
  const product = profile?.product || {};
  const field = (label, value) => value !== undefined && value !== null && value !== '' && <div className="account-dashboard__detail-row" key={label}><strong>{label}</strong><span>{Array.isArray(value) ? value.map((v) => typeof v === 'object' ? Object.entries(v).filter(([, x]) => x !== null && x !== '').map(([k, x]) => `${k.replaceAll('_', ' ')}: ${x}`).join(', ') : v).join(', ') : String(value)}</span></div>;
  return <article className="account-dashboard__case-card account-dashboard__history-item">
    <span className="account-dashboard__case-icon" aria-hidden="true">▤</span>
    <div className="account-dashboard__case-info"><h3>{item.product_name || uiText('Untitled product assessment')}</h3><p>{item.category ? item.category.replaceAll('_', ' ') : uiText('Classification pending')} · {uiText('Updated')} {dateLabel(item.updated_at, currentLang)}</p></div>
    <button type="button" className="account-dashboard__open-case" onClick={toggleDetails}>{loadingDetails ? uiText('Loading your cases…') : details ? uiText('Hide details') : uiText('View details')}</button>
    <button type="button" className="account-dashboard__open-case" onClick={() => onOpenCase(item.session_id)}>{uiText('Open case')}&nbsp; →</button>
    <button type="button" className="account-dashboard__delete-case" onClick={removeCase}>{uiText('Delete')}</button>
    {detailError && <p className="account-dashboard__error" role="alert">{detailError}</p>}
    {details && <section className="account-dashboard__case-details">
      <h4>{uiText('Product and case information')}</h4>
      {field('Product name', product.name)}{field('Jurisdiction', profile.jurisdiction)}{field('Protection target', profile.protection_target)}{field('Composition', product.composition)}{field('Intended use', product.intended_use)}{field('Classical basis', product.classical_basis)}{field('Classical reference', product.classical_reference)}{field('Novelty', product.novelty)}{field('Ingredient sources', product.ingredient_sources)}{field('Biological origin known', product.biological_origin_known)}{field('Origin region', product.biological_origin_region)}{field('Development status', product.development_status)}{field('Objectives', profile.objective)}{field('Classification', profile.classification?.category)}{field('Confidence', profile.classification?.confidence)}{field('Classification reasons', profile.classification?.reasons)}
      <h4>{uiText('Question and answer history')}</h4>
      {details.queries?.length ? details.queries.map((query) => <div className="account-dashboard__query-detail" key={query.id}><strong>{query.question}</strong><p>{query.answer_text || uiText('No answer text was saved.')}</p><small>{dateLabel(query.timestamp, currentLang)}{query.abstained ? ` · ${uiText('Assistant abstained')}` : ''}</small></div>) : <p>{uiText('No questions have been asked in this case.')}</p>}
      {details.assessments?.map((assessment) => <details key={assessment.type} className="account-dashboard__assessment-detail"><summary>{assessment.type.toUpperCase()} {uiText('assessment')}</summary><pre>{JSON.stringify(assessment.data, null, 2)}</pre></details>)}
    </section>}
  </article>;
}
