import { useEffect, useMemo, useState } from 'react';
import ErrorNotice from '../components/ErrorNotice.jsx';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';
import './ABSHelper.css';

const UNKNOWN = 'unknown';
const PROFILE_STATES = ['KNOWN', 'UNKNOWN', 'AMBIGUOUS', 'CONFLICTING'];
const ACTIVITIES = [
  ['research', 'Research'], ['bio_survey', 'Bio-survey'], ['bio_utilisation', 'Bio-utilisation'],
  ['commercial_utilisation', 'Commercial utilisation'], ['resource_transfer', 'Biological resource transfer'],
  ['research_result_transfer', 'Research-result transfer'], ['ipr_application', 'IPR application'],
  ['ipr_grant', 'IPR grant'], ['ipr_commercialisation', 'IPR commercialisation'], ['other', 'Other'],
];

function initialFacts(pip) {
  const current = pip?.abs_facts || {};
  const product = pip?.product || {};
  const sources = product.ingredient_sources || [];
  const origin = product.biological_origin_known === 'yes' && product.biological_origin_region
    ? (/india/i.test(product.biological_origin_region) ? 'india' : 'foreign')
    : UNKNOWN;
  const composition = product.composition || [];
  const hasBio = sources.some((source) => ['plant', 'animal', 'microbial'].includes(source));
  const sourceType = sources.includes('plant') ? 'plant' : sources.includes('animal') ? 'animal' : sources.includes('microbial') ? 'microbial' : UNKNOWN;
  const facts = {
    applicant: { entity_category: UNKNOWN, applicant_type: UNKNOWN, nationality: '', incorporation_country: '', foreign_participation_or_control: null, status: 'UNKNOWN', ...(current.applicant || {}) },
    resource: { biological_resource_involved: hasBio, resource_name: composition.map((item) => item.ingredient).filter(Boolean).join(', '), scientific_name: '', resource_type: sourceType, resource_part: '', quantity: null, unit: '', country_of_origin: origin === 'india' ? 'India' : product.biological_origin_region || '', origin_status: origin, geographical_location: product.biological_origin_region || '', status: origin === 'india' ? 'KNOWN' : 'UNKNOWN', ...(current.resource || {}) },
    access: { access_method: UNKNOWN, source_type: UNKNOWN, cultivated: false, wild_collected: false, artificially_propagated: false, market_or_trader: false, supplier: '', community: '', institution: '', repository_location: '', status: 'UNKNOWN', ...(current.access || {}) },
    tk: { associated_traditional_knowledge: product.classical_basis === 'yes', tk_type: product.classical_basis === 'yes' ? 'codified' : 'unknown', tk_source: product.classical_reference || '', tk_codified: product.classical_basis === 'yes', tk_community_based: false, status: 'UNKNOWN', ...(current.tk || {}) },
    activity: { activities: pip?.objective?.some((item) => ['patentability', 'prior_art'].includes(item)) ? ['ipr_application'] : [], status: 'UNKNOWN', ...(current.activity || {}) },
    ipr: { ipr_stage: pip?.objective?.some((item) => ['patentability', 'prior_art'].includes(item)) ? 'CONSIDERING_IPR' : 'UNKNOWN', ipr_type: 'patent', jurisdiction_filed: '', status: 'UNKNOWN', ...(current.ipr || {}) },
    certificate_of_origin: { certificate_required: false, certificate_available: false, certificate_status: 'NOT_APPLICABLE', issuing_authority: '', note: '', ...(current.certificate_of_origin || {}) },
    transfer: { transfer_involved: false, transfer_type: null, transferee_type: '', transferee_country: '', ...(current.transfer || {}) },
    annual_turnover_inr: current.annual_turnover_inr ?? null,
    is_itpgrfa_crop: current.is_itpgrfa_crop ?? false,
    government_approved_collaboration: current.government_approved_collaboration ?? false,
  };
  return facts;
}

function updateNested(state, group, key, value) {
  return { ...state, [group]: { ...state[group], [key]: value } };
}

function Field({ label, children, hint }) {
  return <label className="abs-form__field"><span>{label}</span>{children}{hint && <small>{hint}</small>}</label>;
}

function Select({ value, onChange, options }) {
  return <select value={value ?? ''} onChange={(event) => onChange(event.target.value)}>
    {options.map(([key, label]) => <option key={key} value={key}>{label}</option>)}
  </select>;
}

function StatusBadge({ value }) {
  const label = String(value || 'unknown').replaceAll('_', ' ').replaceAll('-', ' ');
  return <span className={`abs-result__badge abs-result__badge--${String(value || '').toLowerCase()}`}>{label}</span>;
}

export default function ABSHelper({ state, pip, onFetch, onRestart, currentLang = 'en' }) {
  const { data, loading, error } = state;
  const [facts, setFacts] = useState(() => initialFacts(pip));
  const [showDetails, setShowDetails] = useState(false);
  const [showEvidence, setShowEvidence] = useState(false);
  const uiText = useTranslatedTexts([
    'ABS-aware guidance · Not a live NBA/SBB filing or status service.',
    'Assessment details use your product answers where available. Anything left unknown stays unknown.',
    'Assess ABS pathway', 'Update assessment', 'Applicant and organisation', 'Biological resource and origin',
    'How the resource was accessed', 'Traditional knowledge', 'Activity and IP stage', 'Additional facts',
    'Applicant type', 'Applicant category', 'Country / nationality', 'Country of incorporation',
    'Foreign participation or control?', 'Applicant fact certainty', 'Biological resource involved?', 'Resource name(s)', 'Scientific name', 'Resource part', 'Quantity', 'Unit', 'Resource type',
    'Country/region where sourced', 'Origin status', 'Knowledge status', 'Access method', 'Source type',
    'Supplier / source details', 'Community or provider', 'Institution', 'Repository location', 'Access fact certainty', 'Was the resource cultivated?', 'Was it wild-collected?',
    'Is traditional knowledge associated?', 'Knowledge type', 'Knowledge source / reference',
    'Codified knowledge?', 'Community-based knowledge?', 'Knowledge fact certainty', 'Activities involved', 'Activity fact certainty', 'Current IP stage', 'IP fact certainty', 'IP type', 'IP jurisdiction (if filed)',
    'Annual turnover (INR)', 'ITPGRFA crop?', 'Government-approved collaboration?',
    'Certificate of Origin available?', 'Certificate status', 'Certificate note / issuing authority', 'Resource/research transfer involved?', 'Transfer type',
    'Transferee type', 'Transferee country', 'What this result means', 'What information is still needed',
    'Human review recommended', 'Why review is recommended', 'Facts to resolve', 'Triggered rules', 'Facts used', 'Next steps',
    'Authority and next steps', 'Required forms / documents', 'Evidence and sources', 'Verified',
    'Partially verified', 'Unverified', 'Reassess after updating facts', 'No additional facts are needed for this result.',
    'ABS pathway', 'Current status', 'Potential relevance', 'Estimated benefit sharing',
    'This is an indicative screening result, not an official filing decision.', 'Resource origin conflict',
  ], currentLang);

  useEffect(() => {
    setFacts(initialFacts(pip));
  }, [pip?.session_id]);

  const missingFields = useMemo(() => new Set((data?.missing_information || []).map((item) => item.field_name)), [data]);
  const setGroup = (group, key, value) => setFacts((current) => updateNested(current, group, key, value));
  const setScalar = (key, value) => setFacts((current) => ({ ...current, [key]: value }));
  const submitFacts = () => {
    const cleanFacts = {
      ...facts,
      annual_turnover_inr: facts.annual_turnover_inr === '' || facts.annual_turnover_inr == null ? null : Number(facts.annual_turnover_inr),
      resource: { ...facts.resource, biological_resource_involved: Boolean(facts.resource.biological_resource_involved), quantity: facts.resource.quantity === '' ? null : facts.resource.quantity },
      applicant: { ...facts.applicant, foreign_participation_or_control: facts.applicant.foreign_participation_or_control === '' ? null : facts.applicant.foreign_participation_or_control },
    };
    onFetch(cleanFacts);
  };
  const submit = (event) => { event.preventDefault(); submitFacts(); };

  const toggleActivity = (activity) => {
    const selected = facts.activity.activities || [];
    setGroup('activity', 'activities', selected.includes(activity) ? selected.filter((item) => item !== activity) : [...selected, activity]);
  };

  return (
    <div className="abs-helper">
      <div className="abs-helper__banner">{uiText('ABS-aware guidance · Not a live NBA/SBB filing or status service.')}</div>
      <p className="abs-helper__intro">{uiText('Assessment details use your product answers where available. Anything left unknown stays unknown.')}</p>
      <ErrorNotice error={error} onRetry={submitFacts} onRestart={onRestart} retryLabel={uiText('Reassess after updating facts')} currentLang={currentLang} />

      <form className="abs-form card" onSubmit={submit}>
        <h2>{uiText('Applicant and organisation')}</h2>
        <div className="abs-form__grid">
          <Field label={uiText('Applicant category')}>
            <Select value={facts.applicant.entity_category} onChange={(value) => setGroup('applicant', 'entity_category', value)} options={[[UNKNOWN, 'Unknown / not sure'], ['indian_citizen', 'Indian citizen'], ['indian_company_no_foreign_control', 'Indian company without foreign control'], ['indian_company_with_foreign_control', 'Indian company with foreign control'], ['foreign_entity_or_individual', 'Foreign person or entity'], ['ayush_practitioner', 'AYUSH practitioner']]} />
          </Field>
          <Field label={uiText('Applicant type')}>
            <Select value={facts.applicant.applicant_type} onChange={(value) => setGroup('applicant', 'applicant_type', value)} options={[[UNKNOWN, 'Unknown'], ['individual', 'Individual'], ['company', 'Company'], ['research_institution', 'Research institution'], ['trust_society', 'Trust / society'], ['other', 'Other']]} />
          </Field>
          <Field label={uiText('Country / nationality')}><input value={facts.applicant.nationality || ''} onChange={(event) => setGroup('applicant', 'nationality', event.target.value)} /></Field>
          <Field label={uiText('Country of incorporation')}><input value={facts.applicant.incorporation_country || ''} onChange={(event) => setGroup('applicant', 'incorporation_country', event.target.value)} /></Field>
          <Field label={uiText('Foreign participation or control?')}>
            <Select value={facts.applicant.foreign_participation_or_control == null ? '' : String(facts.applicant.foreign_participation_or_control)} onChange={(value) => setGroup('applicant', 'foreign_participation_or_control', value === '' ? null : value === 'true')} options={[['', 'Unknown'], ['true', 'Yes'], ['false', 'No']]} />
          </Field>
          <Field label={uiText('Applicant fact certainty')}><Select value={facts.applicant.status} onChange={(value) => setGroup('applicant', 'status', value)} options={PROFILE_STATES.map((value) => [value, value.replaceAll('_', ' ')])} /></Field>
        </div>

        <h2>{uiText('Biological resource and origin')}</h2>
        <div className="abs-form__grid">
          <Field label={uiText('Biological resource involved?')}><Select value={facts.resource.status === 'UNKNOWN' && !facts.resource.biological_resource_involved ? UNKNOWN : String(facts.resource.biological_resource_involved)} onChange={(value) => { setGroup('resource', 'biological_resource_involved', value === 'true'); setGroup('resource', 'status', value === UNKNOWN ? 'UNKNOWN' : 'KNOWN'); }} options={[[UNKNOWN, 'Unknown / not sure'], ['true', 'Yes'], ['false', 'No']]} /></Field>
          <Field label={uiText('Resource type')}><Select value={facts.resource.resource_type} onChange={(value) => setGroup('resource', 'resource_type', value)} options={[[UNKNOWN, 'Unknown'], ['plant', 'Plant'], ['animal', 'Animal'], ['microbial', 'Microbial'], ['other_biological', 'Other biological'], ['non_biological', 'Non-biological']]} /></Field>
          <Field label={uiText('Resource name(s)')}><input value={facts.resource.resource_name || ''} onChange={(event) => setGroup('resource', 'resource_name', event.target.value)} /></Field>
          <Field label={uiText('Scientific name')}><input value={facts.resource.scientific_name || ''} onChange={(event) => setGroup('resource', 'scientific_name', event.target.value)} /></Field>
          <Field label={uiText('Resource part')}><input value={facts.resource.resource_part || ''} onChange={(event) => setGroup('resource', 'resource_part', event.target.value)} /></Field>
          <Field label={uiText('Quantity')}><input type="number" min="0" step="any" value={facts.resource.quantity ?? ''} onChange={(event) => setGroup('resource', 'quantity', event.target.value === '' ? null : Number(event.target.value))} /></Field>
          <Field label={uiText('Unit')}><input value={facts.resource.unit || ''} onChange={(event) => setGroup('resource', 'unit', event.target.value)} /></Field>
          <Field label={uiText('Country/region where sourced')} hint={missingFields.has('biological_origin_region') ? data.missing_information.find((item) => item.field_name === 'biological_origin_region')?.why_it_matters : undefined}><input value={facts.resource.country_of_origin || ''} onChange={(event) => { setGroup('resource', 'country_of_origin', event.target.value); setGroup('resource', 'geographical_location', event.target.value); }} /></Field>
          <Field label={uiText('Origin status')}><Select value={facts.resource.origin_status} onChange={(value) => { setGroup('resource', 'origin_status', value); setGroup('resource', 'status', value === UNKNOWN ? 'UNKNOWN' : 'KNOWN'); if (value === 'india') setGroup('resource', 'country_of_origin', 'India'); }} options={[[UNKNOWN, 'Unknown'], ['india', 'India'], ['foreign', 'Outside India']]} /></Field>
          <Field label={uiText('Knowledge status')}><Select value={facts.resource.status} onChange={(value) => setGroup('resource', 'status', value)} options={PROFILE_STATES.map((value) => [value, value.replaceAll('_', ' ')])} /></Field>
        </div>

        <details className="abs-form__details" open={showDetails} onToggle={(event) => setShowDetails(event.currentTarget.open)}>
          <summary>{uiText('Additional facts')}</summary>
          <h3>{uiText('How the resource was accessed')}</h3>
          <div className="abs-form__grid">
            <Field label={uiText('Access method')}><Select value={facts.access.access_method} onChange={(value) => setGroup('access', 'access_method', value)} options={[[UNKNOWN, 'Unknown'], ['direct_field_collection', 'Collected directly'], ['trader_market', 'Trader / market'], ['cultivator', 'Cultivator'], ['repository_institution', 'Repository / institution'], ['other', 'Other']]} /></Field>
            <Field label={uiText('Source type')}><Select value={facts.access.source_type} onChange={(value) => setGroup('access', 'source_type', value)} options={[[UNKNOWN, 'Unknown'], ['cultivated', 'Cultivated'], ['wild_collected', 'Wild collected'], ['artificially_propagated', 'Artificially propagated'], ['market_or_trader', 'Market / trader'], ['supplier', 'Supplier'], ['community', 'Community'], ['institution', 'Institution']]} /></Field>
            <Field label={uiText('Supplier / source details')}><input value={facts.access.supplier || ''} onChange={(event) => setGroup('access', 'supplier', event.target.value)} /></Field>
            <Field label={uiText('Community or provider')}><input value={facts.access.community || ''} onChange={(event) => setGroup('access', 'community', event.target.value)} /></Field>
            <Field label={uiText('Institution')}><input value={facts.access.institution || ''} onChange={(event) => setGroup('access', 'institution', event.target.value)} /></Field>
            <Field label={uiText('Repository location')}><Select value={facts.access.repository_location || ''} onChange={(value) => setGroup('access', 'repository_location', value)} options={[['', 'Unknown / not applicable'], ['in_india', 'India'], ['outside_india', 'Outside India']]} /></Field>
            <Field label={uiText('Access fact certainty')}><Select value={facts.access.status} onChange={(value) => setGroup('access', 'status', value)} options={PROFILE_STATES.map((value) => [value, value.replaceAll('_', ' ')])} /></Field>
            {['cultivated', 'wild_collected', 'artificially_propagated', 'market_or_trader'].map((key) => <label className="abs-form__check" key={key}><input type="checkbox" checked={Boolean(facts.access[key])} onChange={(event) => setGroup('access', key, event.target.checked)} />{uiText(key.replaceAll('_', ' '))}</label>)}
          </div>

          <h3>{uiText('Traditional knowledge')}</h3>
          <div className="abs-form__grid">
            <Field label={uiText('Is traditional knowledge associated?')}><Select value={facts.tk.status === 'UNKNOWN' && !facts.tk.associated_traditional_knowledge ? UNKNOWN : String(facts.tk.associated_traditional_knowledge)} onChange={(value) => { setGroup('tk', 'associated_traditional_knowledge', value === 'true'); setGroup('tk', 'status', value === UNKNOWN ? 'UNKNOWN' : 'KNOWN'); }} options={[[UNKNOWN, 'Unknown / not sure'], ['true', 'Yes'], ['false', 'No']]} /></Field>
            <Field label={uiText('Knowledge type')}><Select value={facts.tk.tk_type} onChange={(value) => setGroup('tk', 'tk_type', value)} options={[[UNKNOWN, 'Unknown'], ['none', 'None known'], ['codified', 'Codified'], ['community', 'Community-based'], ['both', 'Both']]} /></Field>
            <Field label={uiText('Knowledge source / reference')}><input value={facts.tk.tk_source || ''} onChange={(event) => setGroup('tk', 'tk_source', event.target.value)} /></Field>
            <label className="abs-form__check"><input type="checkbox" checked={Boolean(facts.tk.tk_codified)} onChange={(event) => setGroup('tk', 'tk_codified', event.target.checked)} />{uiText('Codified knowledge?')}</label>
            <label className="abs-form__check"><input type="checkbox" checked={Boolean(facts.tk.tk_community_based)} onChange={(event) => setGroup('tk', 'tk_community_based', event.target.checked)} />{uiText('Community-based knowledge?')}</label>
            <Field label={uiText('Knowledge fact certainty')}><Select value={facts.tk.status} onChange={(value) => setGroup('tk', 'status', value)} options={PROFILE_STATES.map((value) => [value, value.replaceAll('_', ' ')])} /></Field>
          </div>

          <h3>{uiText('Activity and IP stage')}</h3>
          <div className="abs-form__activity-list">{ACTIVITIES.map(([key, label]) => <label className="abs-form__check" key={key}><input type="checkbox" checked={(facts.activity.activities || []).includes(key)} onChange={() => toggleActivity(key)} />{label}</label>)}</div>
          <div className="abs-form__grid">
            <Field label={uiText('Activity fact certainty')}><Select value={facts.activity.status} onChange={(value) => setGroup('activity', 'status', value)} options={PROFILE_STATES.map((value) => [value, value.replaceAll('_', ' ')])} /></Field>
            <Field label={uiText('Current IP stage')}><Select value={facts.ipr.ipr_stage} onChange={(value) => setGroup('ipr', 'ipr_stage', value)} options={['UNKNOWN', 'NO_IPR', 'CONSIDERING_IPR', 'PREPARING_APPLICATION', 'IPR_APPLICATION', 'IPR_GRANTED', 'IPR_COMMERCIALISATION'].map((value) => [value, value.replaceAll('_', ' ')])} /></Field>
            <Field label={uiText('IP fact certainty')}><Select value={facts.ipr.status} onChange={(value) => setGroup('ipr', 'status', value)} options={PROFILE_STATES.map((value) => [value, value.replaceAll('_', ' ')])} /></Field>
            <Field label={uiText('IP type')}><input value={facts.ipr.ipr_type || ''} onChange={(event) => setGroup('ipr', 'ipr_type', event.target.value)} /></Field>
            <Field label={uiText('IP jurisdiction (if filed)')}><input value={facts.ipr.jurisdiction_filed || ''} onChange={(event) => setGroup('ipr', 'jurisdiction_filed', event.target.value)} /></Field>
            <Field label={uiText('Annual turnover (INR)')} hint={missingFields.has('annual_turnover_inr') ? data.missing_information.find((item) => item.field_name === 'annual_turnover_inr')?.why_it_matters : 'Leave blank if unknown; benefit sharing will not be guessed.'}><input type="number" min="0" step="any" value={facts.annual_turnover_inr ?? ''} onChange={(event) => setScalar('annual_turnover_inr', event.target.value)} /></Field>
            <Field label={uiText('ITPGRFA crop?')}><Select value={String(facts.is_itpgrfa_crop)} onChange={(value) => setScalar('is_itpgrfa_crop', value === 'true')} options={[[UNKNOWN, 'Unknown'], ['true', 'Yes'], ['false', 'No']]} /></Field>
            <Field label={uiText('Government-approved collaboration?')}><Select value={String(facts.government_approved_collaboration)} onChange={(value) => setScalar('government_approved_collaboration', value === 'true')} options={[[UNKNOWN, 'Unknown'], ['true', 'Yes'], ['false', 'No']]} /></Field>
            <Field label={uiText('Certificate of Origin available?')}><Select value={String(facts.certificate_of_origin.certificate_available)} onChange={(value) => { setGroup('certificate_of_origin', 'certificate_available', value === 'true'); setGroup('certificate_of_origin', 'certificate_status', value === 'true' ? 'PROVIDED' : 'MISSING'); }} options={[[UNKNOWN, 'Unknown'], ['true', 'Yes'], ['false', 'No']]} /></Field>
            <Field label={uiText('Certificate status')}><Select value={facts.certificate_of_origin.certificate_status} onChange={(value) => setGroup('certificate_of_origin', 'certificate_status', value)} options={['NOT_APPLICABLE', 'REQUIRED', 'PROVIDED', 'MISSING'].map((value) => [value, value.replaceAll('_', ' ')])} /></Field>
            <Field label={uiText('Certificate note / issuing authority')}><input value={facts.certificate_of_origin.note || facts.certificate_of_origin.issuing_authority || ''} onChange={(event) => { setGroup('certificate_of_origin', 'note', event.target.value); setGroup('certificate_of_origin', 'issuing_authority', event.target.value); }} /></Field>
            <Field label={uiText('Resource/research transfer involved?')}><Select value={String(facts.transfer.transfer_involved)} onChange={(value) => setGroup('transfer', 'transfer_involved', value === 'true')} options={[[UNKNOWN, 'Unknown'], ['true', 'Yes'], ['false', 'No']]} /></Field>
            <Field label={uiText('Transfer type')}><Select value={facts.transfer.transfer_type || ''} onChange={(value) => setGroup('transfer', 'transfer_type', value || null)} options={ [['', 'Unknown / not applicable'], ['biological_resource', 'Biological resource'], ['research_results', 'Research results'], ['traditional_knowledge', 'Traditional knowledge'], ['IPR', 'IPR'], ['other', 'Other']] } /></Field>
            <Field label={uiText('Transferee type')}><input value={facts.transfer.transferee_type || ''} onChange={(event) => setGroup('transfer', 'transferee_type', event.target.value)} /></Field>
            <Field label={uiText('Transferee country')}><input value={facts.transfer.transferee_country || ''} onChange={(event) => setGroup('transfer', 'transferee_country', event.target.value)} /></Field>
          </div>
        </details>
        <button className="abs-helper__refresh abs-form__submit" type="submit" disabled={loading}>{uiText(data ? 'Update assessment' : 'Assess ABS pathway')}</button>
      </form>

      {loading && <p className="abs-helper__status">{uiText('Checking Access & Benefit-Sharing relevance…')}</p>}

      {data && (
        <section className="abs-result card" aria-live="polite">
          <div className="abs-result__heading">
            <div><p className="abs-result__eyebrow">{uiText('What this result means')}</p><h2>{uiText('ABS pathway')}</h2></div>
            <StatusBadge value={data.status} />
          </div>
          <div className="abs-result__summary">
            <p><strong>{uiText('ABS pathway')}:</strong> {String(data.pathway || 'UNRESOLVED').replaceAll('_', ' ')}</p>
            <p><strong>{uiText('Potential relevance')}:</strong> <StatusBadge value={data.relevance} /></p>
            {data.abstained && <p className="abs-result__caution">{data.abstain_reason || uiText('This is an indicative screening result, not an official filing decision.')}</p>}
          </div>
          {data.missing_information?.length > 0 && <div className="abs-result__panel abs-result__panel--missing"><h3>{uiText('What information is still needed')}</h3><ul>{data.missing_information.map((item) => <li key={item.field_name}><strong>{item.prompt_question}</strong><p>{item.impact_description} {item.why_it_matters}</p></li>)}</ul></div>}
          {data.human_escalation?.human_review && <div className="abs-result__panel abs-result__panel--review"><h3>{uiText('Human review recommended')}</h3><p>{data.human_escalation.reason || uiText('This case needs a qualified reviewer.')}</p>{data.human_escalation.case_summary && <p>{data.human_escalation.case_summary}</p>}{data.human_escalation.conflicts?.length > 0 && <><h4>{uiText('Facts to resolve')}</h4><ul>{data.human_escalation.conflicts.map((item, index) => <li key={index}>{item}</li>)}</ul></>}{data.human_escalation.missing_facts?.length > 0 && <p>{data.human_escalation.missing_facts.join(', ')}</p>}</div>}
          {data.reasoning?.length > 0 && <div className="abs-result__panel"><h3>{uiText('What this result means')}</h3><ul>{data.reasoning.map((item, index) => <li key={index}>{item}</li>)}</ul></div>}
          {data.facts_considered && Object.keys(data.facts_considered).length > 0 && <details className="abs-result__evidence"><summary>{uiText('Facts used')}</summary><dl className="abs-result__facts">{Object.entries(data.facts_considered).map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{Array.isArray(value) ? value.join(', ') || '—' : String(value ?? '—').replaceAll('_', ' ')}</dd></div>)}</dl></details>}
          {data.triggered_rules?.length > 0 && <div className="abs-result__panel"><h3>{uiText('Triggered rules')}</h3><ul>{data.triggered_rules.map((rule) => <li key={rule.rule_id}><strong>{rule.rule_id} · {rule.rule_name}</strong><p>{rule.section_or_rule} — {rule.description}</p></li>)}</ul></div>}
          {data.authority_routing && <div className="abs-result__panel"><h3>{uiText('Authority and next steps')}</h3><p><strong>{data.authority_routing.authority_name}</strong> · {data.authority_routing.jurisdiction_scope}</p><ul>{(data.authority_routing.reasons || []).map((item, index) => <li key={index}>{item}</li>)}</ul></div>}
          {data.form_requirements?.length > 0 && <div className="abs-result__panel"><h3>{uiText('Required forms / documents')}</h3><ul>{data.form_requirements.map((item) => <li key={item.form_id}><strong>{item.form_name}</strong>: {item.purpose}</li>)}</ul></div>}
          {data.next_actions?.length > 0 && <div className="abs-result__panel"><h3>{uiText('Next steps')}</h3><ul>{data.next_actions.map((item, index) => <li key={index}>{item}</li>)}</ul></div>}
          {data.benefit_sharing?.calculation_status && <div className="abs-result__panel"><h3>{uiText('Estimated benefit sharing')}</h3><p>{data.benefit_sharing.calculation_status.replaceAll('_', ' ')}{data.benefit_sharing.rate_or_slab ? ` · ${data.benefit_sharing.rate_or_slab}` : ''}{data.benefit_sharing.indicative_amount_inr != null ? ` · ₹${Number(data.benefit_sharing.indicative_amount_inr).toLocaleString('en-IN')}` : ''}</p><small>{data.benefit_sharing.disclaimer}</small></div>}
          <details className="abs-result__evidence"><summary>{uiText('Evidence and sources')} ({(data.citations || []).length})</summary><ul>{(data.citations || []).map((citation, index) => <li key={`${citation.doc_id}-${citation.section_or_article}-${index}`}><div><strong>{citation.document_name}</strong> · {citation.section_or_article} <StatusBadge value={citation.verification_status} /></div><p>{citation.excerpt}</p>{citation.source_url && <a href={citation.source_url} target="_blank" rel="noreferrer">{citation.source_url}</a>}</li>)}</ul>{data.grounded_reasoning?.length > 0 && <h4>Retrieved corpus matches</h4>}{data.grounded_reasoning?.map((item, index) => <p key={index}>{item.reasoning_text} — {item.verified ? uiText('Verified') : uiText('Unverified')}{item.document_name ? ` · ${item.document_name}` : ''}</p>)}</details>
          <p className="abs-result__disclaimer">{uiText(data.disclaimer || 'This is an indicative screening result, not an official filing decision.')}</p>
        </section>
      )}
    </div>
  );
}
