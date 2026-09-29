import { useEffect, useState } from 'react';
import { searchDataset } from '../api/client.js';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';
import './DatasetExplorer.css';

const PAGE_SIZE = 50;
const DATASETS = [
  { key: 'legal', label: 'Legal Corpus', short: 'Acts, rules and treaties' },
  { key: 'nba', label: 'NBA & ABS', short: 'Biodiversity and benefit sharing' },
  { key: 'tkdl', label: 'TKDL Archive', short: 'Traditional knowledge records' },
];
const DATASET_INFO = {
  legal: { title: 'Legal Corpus', eyebrow: 'STATUTES · RULES · TREATIES', intro: 'Browse the source material used by the assistant. Search by law, section, subject, or keyword.' },
  nba: { title: 'NBA & ABS Sources', eyebrow: 'INDIA · BIODIVERSITY & BENEFIT SHARING', intro: 'Read the Indian biodiversity and ABS legal material relevant to NBA/SBB pathways. This is not an NBA registry or filing tracker.' },
  tkdl: { title: 'TKDL Archive', eyebrow: 'OFFLINE · SOURCE-DERIVED FORMULATIONS', intro: 'Browse offline source-derived formulation records. This is not a live connection to the Traditional Knowledge Digital Library.' },
};

function splitForTranslation(value, limit = 650) {
  const parts = [];
  let remaining = (value || '').trim();
  while (remaining.length > limit) {
    let cut = remaining.lastIndexOf(' ', limit);
    if (cut < Math.floor(limit * 0.6)) cut = limit;
    parts.push(remaining.slice(0, cut));
    remaining = remaining.slice(cut).trim();
  }
  if (remaining) parts.push(remaining);
  return parts;
}

function SourceReader({ item, dataset, uiText, currentLang }) {
  const body = (item.text || '').replace(/^---[\s\S]*?---\s*/, '').trim();
  const sourceText = dataset === 'tkdl' ? (item.source_text || '') : body;
  const sourceParts = splitForTranslation(sourceText);
  const translatedData = useTranslatedTexts([
    item.document_name, item.document_type, item.status_note,
    item.formulation_name, item.formulation_type, item.source_text,
    ...(item.therapeutic_use || []), ...sourceParts,
    ...(item.ingredients || []).flatMap((ingredient) => [ingredient.part_used, ingredient.processing]),
  ].filter(Boolean), currentLang);
  if (dataset === 'tkdl') {
    return <article className="dataset-explorer__reader-entry">
      <div className="dataset-explorer__record-head"><span>{item.record_id}</span><span>{translatedData(item.formulation_type || 'Formulation')}</span></div>
      <h2>{translatedData(item.formulation_name || 'Unnamed formulation')}</h2>
      <dl className="dataset-explorer__metadata"><div><dt>{uiText('Source')}</dt><dd>{item.source_text ? translatedData(item.source_text) : uiText('Not specified in this record')}</dd></div>{item.therapeutic_use?.length > 0 && <div><dt>{uiText('Traditional use')}</dt><dd>{item.therapeutic_use.map(translatedData).join('; ')}</dd></div>}</dl>
      <section className="dataset-explorer__ingredients"><h3>{uiText('Ingredients')} ({item.ingredients?.length || 0})</h3>{item.ingredients?.length ? <ul>{item.ingredients.map((ingredient, index) => <li key={`${ingredient.name}-${index}`}><strong>{ingredient.name}</strong>{ingredient.scientific_name ? ` · ${ingredient.scientific_name}` : ''}{ingredient.traditional_name ? ` · ${ingredient.traditional_name}` : ''}{ingredient.part_used ? ` · ${uiText('Part used')}: ${translatedData(ingredient.part_used)}` : ''}{ingredient.processing ? ` · ${uiText('Processing')}: ${translatedData(ingredient.processing)}` : ''}</li>)}</ul> : <p>{uiText('No ingredient data is available in this record.')}</p>}</section>
    </article>;
  }

  const source = item.source_url?.startsWith('http') ? item.source_url : null;
  return <article className="dataset-explorer__reader-entry">
    <div className="dataset-explorer__record-head"><span>{item.jurisdiction === 'india' ? 'INDIA' : 'INTERNATIONAL'}</span><span>{item.legal_regime?.replaceAll('_', ' ')}</span></div>
    <h2>{translatedData(item.document_name)}</h2>
    <p className="dataset-explorer__section">{item.section_or_article || item.document_type}</p>
    <p className="dataset-explorer__meta">{translatedData(item.document_type)}{item.date_enacted ? ` · ${item.date_enacted}` : ''}{item.last_verified_date ? ` · ${uiText('Verified')} ${item.last_verified_date}` : ''}</p>
    {item.status_note && <p className="dataset-explorer__note">{uiText('Source note')}: {translatedData(item.status_note)}</p>}
    <section className="dataset-explorer__source">
      <h3>{uiText('Source text')}</h3>
      {currentLang !== 'en' && body && <><h4>{uiText('Unofficial machine translation')}</h4><div>{sourceParts.map(translatedData).join(' ')}</div><p>{uiText('The original source text follows.')}</p></>}
      <div>{body || uiText('No source text is available for this entry.')}</div>
    </section>
    {source && <a className="dataset-explorer__source-link" href={source} target="_blank" rel="noreferrer">{uiText('Open official source')} ↗</a>}
  </article>;
}

export default function DatasetExplorer({ dataset, onChangeDataset, currentLang = 'en' }) {
  const info = DATASET_INFO[dataset] || DATASET_INFO.legal;
  const [draft, setDraft] = useState('');
  const [query, setQuery] = useState('');
  const [jurisdiction, setJurisdiction] = useState('all');
  const [page, setPage] = useState(0);
  const [result, setResult] = useState({ items: [], total: 0, description: '' });
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const uiText = useTranslatedTexts([
    'VEDAVERSE SOURCE LIBRARY', 'Information only · Not legal advice', 'Choose a source collection',
    ...DATASETS.flatMap((item) => [item.label, item.short]),
    ...Object.values(DATASET_INFO).flatMap((item) => [item.title, item.eyebrow, item.intro]),
    'Search names, sections, ingredients, keywords', 'Search dataset', 'Search', 'All jurisdictions',
    'Loading catalogue…', 'entries', 'No matching entries', 'Try a broader search term.',
    'Source entries', 'Select an entry to read its source details.', 'Previous', 'Next', 'Page', 'Source',
    'Not specified in this record', 'Traditional use', 'Ingredients', 'Part used', 'Processing',
    'No ingredient data is available in this record.', 'Source text', 'No source text is available for this entry.',
    'Open official source',
    'Verified', 'Source note', 'Unofficial machine translation', 'The original source text follows.',
    ...result.items.flatMap((item) => [
      item.document_name, item.formulation_name, item.formulation_type,
      item.section_or_article, item.document_type,
    ]),
    result.description,
  ], currentLang);

  useEffect(() => { setDraft(''); setQuery(''); setPage(0); setJurisdiction('all'); setSelected(null); }, [dataset]);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError('');
    searchDataset(dataset, query, PAGE_SIZE, page * PAGE_SIZE, jurisdiction)
      .then((data) => {
        if (active) {
          setResult(data);
          setSelected(data.items[0] || null);
        }
      })
      .catch((err) => { if (active) setError(err.message || 'Could not load this source catalogue.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [dataset, query, page, jurisdiction]);

  const submitSearch = (event) => { event.preventDefault(); setPage(0); setQuery(draft.trim()); };
  const pageCount = Math.max(1, Math.ceil(result.total / PAGE_SIZE));

  return <section className="dataset-explorer" aria-label="Source library">
    <div className="dataset-explorer__library-label"><span className="dataset-explorer__book-icon" aria-hidden="true">▤</span><span>{uiText('VEDAVERSE SOURCE LIBRARY')}</span><span className="dataset-explorer__library-divider" /><span className="dataset-explorer__library-disclaimer">{uiText('Information only · Not legal advice')}</span></div>
    <nav className="dataset-explorer__collections" aria-label={uiText('Choose a source collection')}>{DATASETS.map((item) => <button key={item.key} type="button" onClick={() => onChangeDataset?.(item.key)} className={dataset === item.key ? 'is-active' : ''}><strong>{uiText(item.label)}</strong><small>{uiText(item.short)}</small></button>)}</nav>
    <header className="dataset-explorer__header"><div><p>{uiText(info.eyebrow)}</p><h1>{uiText(info.title)}</h1><div>{uiText(info.intro)}</div></div></header>
    <form className="dataset-explorer__search" onSubmit={submitSearch}><label className="dataset-explorer__searchbox"><span aria-hidden="true">⌕</span><input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder={uiText('Search names, sections, ingredients, keywords')} aria-label={uiText('Search dataset')} /><button type="submit">{uiText('Search')}</button></label>{dataset === 'legal' && <select value={jurisdiction} aria-label={uiText('Filter by jurisdiction')} onChange={(event) => { setPage(0); setJurisdiction(event.target.value); }}><option value="all">{uiText('All jurisdictions')}</option><option value="india">{uiText('India')}</option><option value="international">{uiText('International')}</option></select>}</form>
    <div className="dataset-explorer__summary"><strong>{loading ? uiText('Loading catalogue…') : `${result.total} ${uiText('entries')}`}</strong><span>{uiText(result.description)}</span></div>
    {error && <div className="dataset-explorer__error" role="alert">{error}</div>}
    {!loading && !error && result.items.length === 0 && <div className="dataset-explorer__empty"><h2>{uiText('No matching entries')}</h2><p>{uiText('Try a broader search term.')}</p></div>}
    {!error && result.items.length > 0 && <div className="dataset-explorer__reader">
      <nav className="dataset-explorer__entry-list" aria-label={uiText('Source entries')}>{result.items.map((item, index) => {
        const title = dataset === 'tkdl' ? item.formulation_name : item.document_name;
        const subtitle = dataset === 'tkdl' ? `${item.formulation_type || 'Formulation'} · ${item.record_id}` : (item.section_or_article || item.document_type);
        const isSelected = selected === item;
        return <button type="button" key={item.record_id || `${item.doc_id}-${item.corpus_path}-${index}`} onClick={() => setSelected(item)} className={`dataset-explorer__entry${isSelected ? ' is-selected' : ''}`} aria-current={isSelected ? 'true' : undefined}><span className="dataset-explorer__entry-marker">{dataset === 'tkdl' ? '✦' : '§'}</span><span><strong>{uiText(title || 'Untitled source')}</strong><small>{uiText(subtitle)}</small></span><span className="dataset-explorer__entry-arrow">›</span></button>;
      })}</nav>
      <div className="dataset-explorer__reading-pane">{selected ? <SourceReader item={selected} dataset={dataset} uiText={uiText} currentLang={currentLang} /> : <p>{uiText('Select an entry to read its source details.')}</p>}</div>
    </div>}
    {result.total > PAGE_SIZE && <nav className="dataset-explorer__pagination" aria-label="Dataset pages"><button type="button" onClick={() => setPage((number) => Math.max(0, number - 1))} disabled={page === 0}>← {uiText('Previous')}</button><span>{uiText('Page')} {page + 1} of {pageCount}</span><button type="button" onClick={() => setPage((number) => Math.min(pageCount - 1, number + 1))} disabled={page + 1 >= pageCount}>{uiText('Next')} →</button></nav>}
  </section>;
}
