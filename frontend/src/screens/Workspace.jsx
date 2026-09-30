import QueryWorkspace from './QueryWorkspace.jsx';
import TKDLSearch from './TKDLSearch.jsx';
import ABSHelper from './ABSHelper.jsx';
import ConfidenceTrend from '../components/ConfidenceTrend.jsx';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';
import './Workspace.css';

export default function Workspace({
  pip,
  classification,
  queryHistory,
  queryLoading,
  queryError,
  onAsk,
  onAddTurn,
  onOpenCitation,
  tkdl,
  onFetchTkdl,
  abs,
  onFetchAbs,
  onRestart,
  onEndCase,
  canEndCase = true,
  currentLang = 'en',
  tab = 'query',
  onTabChange,
}) {
  const uiText = useTranslatedTexts(['Ask & Explore', 'TKDL Match', 'ABS Helper', 'End case', 'End this case and add it to Case History.'], currentLang);
  return (
    <div className="workspace-shell">
      <div className="workspace-shell__layout">
      <div className="workspace-shell__main">
      <nav className="workspace-shell__tabs" aria-label="Case tools">
        {[
          ['query', 'Ask & Explore'],
          ['tkdl', 'TKDL Match'],
          ['abs', 'ABS Helper'],
        ].map(([key, label]) => <button key={key} type="button" onClick={() => onTabChange?.(key)} className={`workspace-shell__tab${tab === key ? ' workspace-shell__tab--active' : ''}`}>{uiText(label)}</button>)}
      </nav>
      {tab === 'query' && (
        <QueryWorkspace
          pip={pip}
          classification={classification}
          history={Array.isArray(queryHistory) ? queryHistory : []}
          onAsk={onAsk}
          onAddTurn={onAddTurn}
          loading={queryLoading}
          error={queryError}
          onOpenCitation={onOpenCitation}
          onRestart={onRestart}
          currentLang={currentLang}
        />
      )}

      {tab === 'tkdl' && (
        <TKDLSearch
          state={tkdl}
          onFetch={onFetchTkdl}
          onRestart={onRestart}
          currentLang={currentLang}
        />
      )}

      {tab === 'abs' && (
        <ABSHelper
          state={abs}
          pip={pip}
          onFetch={onFetchAbs}
          onRestart={onRestart}
          currentLang={currentLang}
        />
      )}

      </div>
      <aside className="workspace-shell__aside" aria-label="Confidence">
        <ConfidenceTrend history={Array.isArray(queryHistory) ? queryHistory : []} currentLang={currentLang} />
      </aside>
      </div>

      {canEndCase && <div className="workspace-shell__end-case"><span>{uiText('End this case and add it to Case History.')}</span><button type="button" onClick={onEndCase} disabled={queryLoading}>{uiText('End case')}</button></div>}

    </div>
  );
}
