import { useState } from 'react';
import QueryWorkspace from './QueryWorkspace.jsx';
import TKDLSearch from './TKDLSearch.jsx';
import ABSHelper from './ABSHelper.jsx';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';
import './Workspace.css';

const TABS = [
  { key: 'query', label: 'Ask & Explore' },
  { key: 'tkdl', label: 'TKDL Search' },
  { key: 'abs', label: 'ABS Helper' },
];

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
  currentLang = 'en',
}) {
  const [tab, setTab] = useState('query');
  const uiText = useTranslatedTexts(TABS.map((item) => item.label), currentLang);

  return (
    <div className="workspace-shell">
      <div className="workspace-shell__tabs" role="tablist">
        {TABS.map((tb) => (
          <button
            key={tb.key}
            type="button"
            role="tab"
            aria-selected={tab === tb.key}
            className={
              'workspace-shell__tab' + (tab === tb.key ? ' workspace-shell__tab--active' : '')
            }
            onClick={() => setTab(tb.key)}
          >
            {uiText(tb.label)}
          </button>
        ))}
      </div>

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
          onFetch={onFetchAbs}
          onRestart={onRestart}
          currentLang={currentLang}
        />
      )}

    </div>
  );
}
