import { useState } from 'react';
import QueryWorkspace from './QueryWorkspace.jsx';
import TKDLSearch from './TKDLSearch.jsx';
import ABSHelper from './ABSHelper.jsx';
import './Workspace.css';

/**
 * Part 3 — tab container for the three "workspace" screens (build spec §15
 * items 5/8/9: Query/Answer, TKDL Search, ABS Helper). Sits inside the
 * wizard's existing 'workspace' step — AppHeader's stepper still just
 * shows "Ask & Explore" as one step; these are sub-navigation within it,
 * not new top-level wizard steps.
 *
 * Purely a tab switcher: every backend-touching prop is passed straight
 * through to the three real screens, same pattern as everywhere else —
 * this file itself never calls api/client.js.
 */
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
  onOpenCitation,
  tkdl,
  onFetchTkdl,
  abs,
  onFetchAbs,
  onRestart,
}) {
  const [tab, setTab] = useState('query');

  return (
    <div className="workspace-shell">
      <div className="workspace-shell__tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={tab === t.key}
            className={
              'workspace-shell__tab' + (tab === t.key ? ' workspace-shell__tab--active' : '')
            }
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'query' && (
        <QueryWorkspace
          pip={pip}
          classification={classification}
          history={queryHistory}
          onAsk={onAsk}
          loading={queryLoading}
          error={queryError}
          onOpenCitation={onOpenCitation}
          onRestart={onRestart}
        />
      )}

      {tab === 'tkdl' && <TKDLSearch state={tkdl} onFetch={onFetchTkdl} onRestart={onRestart} />}

      {tab === 'abs' && <ABSHelper state={abs} onFetch={onFetchAbs} onRestart={onRestart} />}
    </div>
  );
}
