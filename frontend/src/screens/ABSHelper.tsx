import { useState, useEffect } from 'react'
import type { ABSAssessResponse, ABSFactProfileInput } from '../types'
import { absAssessAPI } from '../api'
import { Button } from '../components/Button'

interface ABSHelperProps {
  sessionId: string
  onBack: () => void
}

export function ABSHelper({ sessionId, onBack }: ABSHelperProps) {
  const [data, setData] = useState<ABSAssessResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [absFacts, setAbsFacts] = useState<ABSFactProfileInput>({
    applicant: { entity_category: 'unknown' },
    resource: { biological_resource_involved: true, resource_type: 'plant', origin_status: 'india' },
    access: { source_type: 'unknown', cultivated: false },
    tk: { tk_type: 'none', tk_codified: false, tk_community_based: false },
    activity: { activities: [] },
    ipr: { ipr_stage: 'UNKNOWN' },
    certificate_of_origin: { certificate_available: false },
    annual_turnover_inr: undefined,
  })
  const [showFactEditor, setShowFactEditor] = useState(false)

  const fetchAssessment = (facts?: ABSFactProfileInput) => {
    setLoading(true)
    setError(false)
    absAssessAPI(sessionId, facts)
      .then((res) => {
        setData(res)
        setLoading(false)
      })
      .catch(() => {
        setError(true)
        setLoading(false)
      })
  }

  useEffect(() => {
    fetchAssessment()
  }, [sessionId])

  const handleFactUpdate = (patch: Partial<ABSFactProfileInput>) => {
    const updated: ABSFactProfileInput = {
      ...absFacts,
      ...patch,
      applicant: { ...absFacts.applicant, ...patch.applicant },
      resource: { ...absFacts.resource, ...patch.resource },
      access: { ...absFacts.access, ...patch.access },
      tk: { ...absFacts.tk, ...patch.tk },
      activity: { ...absFacts.activity, ...patch.activity },
      ipr: { ...absFacts.ipr, ...patch.ipr },
      certificate_of_origin: { ...absFacts.certificate_of_origin, ...patch.certificate_of_origin },
    }
    setAbsFacts(updated)
    fetchAssessment(updated)
  }

  const isCommercial = absFacts.activity?.activities?.includes('commercial_utilisation') ||
                      absFacts.activity?.activities?.includes('ipr_commercialisation') ||
                      absFacts.ipr?.ipr_stage === 'IPR_COMMERCIALISATION'

  const isCultivated = absFacts.access?.source_type === 'cultivated' || absFacts.access?.cultivated === true

  return (
    <div className="fade-in" style={{ paddingBottom: '40px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="section-title">ABS Regulatory Pathway Engine</h1>
          <p className="section-subtitle">
            Traceable legal compliance, statutory pathways & benefit-sharing decision support.
          </p>
        </div>
        <Button variant="default" onClick={() => setShowFactEditor(!showFactEditor)}>
          {showFactEditor ? 'Hide Adaptive Questionnaire' : 'Adaptive Intake Questionnaire'}
        </Button>
      </div>

      <div className="demo-banner" style={{ marginTop: '16px' }}>
        Fact-driven deterministic legal engine based on India's Biological Diversity Act 2002 (as amended 2023) & 2024 Rules.
      </div>

      {/* Adaptive Conditional Questionnaire Panel */}
      {showFactEditor && (
        <div className="card card-padded" style={{ marginTop: '16px', background: 'var(--c-surface)', border: '1px solid var(--c-primary-light)' }}>
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--c-primary)', marginBottom: '4px' }}>
            Adaptive ABS Intake Questionnaire
          </h3>
          <p style={{ fontSize: '12px', color: 'var(--c-text-muted)', marginBottom: '16px' }}>
            Dynamically asks relevant questions based on your selections. Reuses stored product facts.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            {/* Step 1: Biological Resource */}
            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--c-text-muted)' }}>1. Biological Resource Involved?</label>
              <select
                style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid var(--c-border)', marginTop: '4px' }}
                value={absFacts.resource?.biological_resource_involved ? 'yes' : 'no'}
                onChange={(e) => handleFactUpdate({ resource: { biological_resource_involved: e.target.value === 'yes' } })}
              >
                <option value="yes">Yes (Plant / Animal / Microbial)</option>
                <option value="no">No (Mineral / Purely Synthetic)</option>
              </select>
            </div>

            {/* Step 1b: Resource Type (Conditional) */}
            {absFacts.resource?.biological_resource_involved && (
              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--c-text-muted)' }}>Resource Type</label>
                <select
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid var(--c-border)', marginTop: '4px' }}
                  value={absFacts.resource?.resource_type ?? 'plant'}
                  onChange={(e) => handleFactUpdate({ resource: { resource_type: e.target.value } })}
                >
                  <option value="plant">Plant Material / Botanicals</option>
                  <option value="animal">Animal Derivative</option>
                  <option value="microbial">Microorganism / Microbial Strain</option>
                  <option value="other_biological">Other Biological</option>
                </select>
              </div>
            )}

            {/* Step 2: Biological Origin (Conditional) */}
            {absFacts.resource?.biological_resource_involved && (
              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--c-text-muted)' }}>2. Country of Origin</label>
                <select
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid var(--c-border)', marginTop: '4px' }}
                  value={absFacts.resource?.origin_status ?? 'india'}
                  onChange={(e) => handleFactUpdate({ resource: { origin_status: e.target.value, country_of_origin: e.target.value === 'foreign' ? 'Outside India' : 'India' } })}
                >
                  <option value="india">India (Domestic Species)</option>
                  <option value="foreign">Outside India (Foreign Species)</option>
                  <option value="unknown">Unknown / Unverified</option>
                </select>
              </div>
            )}

            {/* Step 3: Applicant Category */}
            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--c-text-muted)' }}>3. Applicant Entity Category</label>
              <select
                style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid var(--c-border)', marginTop: '4px' }}
                value={absFacts.applicant?.entity_category ?? 'unknown'}
                onChange={(e) => handleFactUpdate({ applicant: { entity_category: e.target.value } })}
              >
                <option value="unknown">Unknown / Unspecified</option>
                <option value="indian_citizen">Indian Citizen</option>
                <option value="indian_company_no_foreign_control">Indian Company (100% Indian Shareholding)</option>
                <option value="indian_company_with_foreign_control">Indian Company (Foreign Shareholding/Control)</option>
                <option value="foreign_entity_or_individual">Foreign Entity / Non-Indian Individual</option>
                <option value="ayush_practitioner">Registered AYUSH Practitioner</option>
              </select>
            </div>

            {/* Step 4: Access / Source */}
            {absFacts.resource?.biological_resource_involved && (
              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--c-text-muted)' }}>4. Access / Procurement Source</label>
                <select
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid var(--c-border)', marginTop: '4px' }}
                  value={absFacts.access?.source_type ?? 'unknown'}
                  onChange={(e) =>
                    handleFactUpdate({
                      access: {
                        source_type: e.target.value,
                        cultivated: e.target.value === 'cultivated',
                      },
                    })
                  }
                >
                  <option value="unknown">Unknown Source</option>
                  <option value="cultivated">Cultivated Medicinal Plant</option>
                  <option value="wild_collected">Wild Field Collection</option>
                  <option value="market_or_trader">Market / Local Trader (NTC Commodity)</option>
                  <option value="institution">Repository / Institution / Culture Collection</option>
                </select>
              </div>
            )}

            {/* Step 4b: Certificate of Origin (Conditional on Cultivated) */}
            {isCultivated && (
              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--c-text-muted)' }}>Certificate of Origin Available?</label>
                <select
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid var(--c-border)', marginTop: '4px' }}
                  value={absFacts.certificate_of_origin?.certificate_available ? 'yes' : 'no'}
                  onChange={(e) => handleFactUpdate({ certificate_of_origin: { certificate_available: e.target.value === 'yes' } })}
                >
                  <option value="no">No / Missing Certificate</option>
                  <option value="yes">Yes (Issued by Agriculture/Forest Dept)</option>
                </select>
              </div>
            )}

            {/* Step 5: Traditional Knowledge */}
            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--c-text-muted)' }}>5. Traditional Knowledge (TK) Status</label>
              <select
                style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid var(--c-border)', marginTop: '4px' }}
                value={absFacts.tk?.tk_type ?? 'none'}
                onChange={(e) =>
                  handleFactUpdate({
                    tk: {
                      tk_type: e.target.value,
                      tk_codified: e.target.value === 'codified' || e.target.value === 'both',
                      tk_community_based: e.target.value === 'community' || e.target.value === 'both',
                    },
                  })
                }
              >
                <option value="none">No Associated Traditional Knowledge</option>
                <option value="codified">Codified Text (Ayurveda / Siddha / Unani Formulations)</option>
                <option value="community">Uncodified Community Traditional Knowledge</option>
                <option value="both">Both Codified and Community Knowledge</option>
              </select>
            </div>

            {/* Step 6: Intended Activity */}
            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--c-text-muted)' }}>6. Primary Intended Activity</label>
              <select
                style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid var(--c-border)', marginTop: '4px' }}
                value={absFacts.activity?.activities?.[0] ?? 'research'}
                onChange={(e) => handleFactUpdate({ activity: { activities: [e.target.value] } })}
              >
                <option value="research">Basic Academic / Scientific Research</option>
                <option value="commercial_utilisation">Commercial Utilisation & Manufacturing</option>
                <option value="bio_utilisation">Bio-survey & Bio-utilisation</option>
                <option value="research_result_transfer">Transfer of Research Results to Foreign Entity</option>
                <option value="resource_transfer">Third-Party Transfer of Accessed Resource</option>
              </select>
            </div>

            {/* Step 7: IPR Lifecycle Stage */}
            <div>
              <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--c-text-muted)' }}>7. IPR Lifecycle Stage</label>
              <select
                style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid var(--c-border)', marginTop: '4px' }}
                value={absFacts.ipr?.ipr_stage ?? 'NO_IPR'}
                onChange={(e) => handleFactUpdate({ ipr: { ipr_stage: e.target.value } })}
              >
                <option value="NO_IPR">No IPR Filing Intended</option>
                <option value="CONSIDERING_IPR">Considering / Evaluating IP Filing</option>
                <option value="PREPARING_APPLICATION">Preparing Patent Specification</option>
                <option value="IPR_APPLICATION">Patent Application Pending Filing</option>
                <option value="IPR_GRANTED">Patent Granted</option>
                <option value="IPR_COMMERCIALISATION">Commercialising Granted Patent</option>
              </select>
            </div>

            {/* Step 8: Estimated Turnover (Conditional on Commercialisation) */}
            {isCommercial && (
              <div>
                <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--c-text-muted)' }}>8. Annual Turnover / Ex-Factory Sales (INR)</label>
                <input
                  type="number"
                  placeholder="e.g. 20000000"
                  style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid var(--c-border)', marginTop: '4px' }}
                  value={absFacts.annual_turnover_inr ?? ''}
                  onChange={(e) => handleFactUpdate({ annual_turnover_inr: e.target.value ? parseFloat(e.target.value) : undefined })}
                />
              </div>
            )}
          </div>
        </div>
      )}

      {loading && (
        <div className="card card-padded" style={{ marginTop: '24px', textAlign: 'center', padding: '48px' }}>
          <div className="spinner" />
          <p style={{ marginTop: '16px', color: 'var(--c-text-muted)', fontSize: '14px' }}>
            Evaluating deterministic ABS regulatory pathways...
          </p>
        </div>
      )}

      {error && (
        <div className="card card-padded error-state" style={{ marginTop: '24px' }}>
          <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--c-error)', marginBottom: '8px' }}>
            Service Error
          </div>
          <p style={{ fontSize: '14px', color: 'var(--c-text-secondary)' }}>
            Unable to connect to the ABS regulatory engine. Please check your backend connection.
          </p>
          <Button variant="primary" style={{ marginTop: '16px' }} onClick={() => fetchAssessment(absFacts)}>
            Retry
          </Button>
        </div>
      )}

      {!loading && !error && data && (
        <>
          {/* Header Verdict & Status Badges */}
          <div className="card card-padded" style={{ marginTop: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--c-text-muted)', textTransform: 'uppercase' }}>
                  Statutory Pathway
                </div>
                <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--c-primary)', marginTop: '4px' }}>
                  {data.pathway ?? 'UNRESOLVED'}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                {data.status && (
                  <span className={`abs-status-badge abs-status-${data.status}`}>
                    {data.status.replace(/_/g, ' ')}
                  </span>
                )}
                <span className={`abs-badge abs-${data.relevance}`}>
                  {data.relevance.replace(/_/g, ' ').toUpperCase()}
                </span>
              </div>
            </div>

            {/* Facts Considered Grid */}
            {data.facts_considered && (
              <div style={{ marginTop: '16px', borderTop: '1px solid var(--c-border)', paddingTop: '16px' }}>
                <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--c-text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
                  Facts Considered
                </div>
                <div className="abs-fact-grid">
                  <div className="abs-fact-card">
                    <div className="abs-fact-label">Applicant Entity</div>
                    <div className="abs-fact-value">{String(data.facts_considered.entity_category ?? 'Unknown').replace(/_/g, ' ')}</div>
                  </div>
                  <div className="abs-fact-card">
                    <div className="abs-fact-label">Resource Type</div>
                    <div className="abs-fact-value">{String(data.facts_considered.resource_type ?? 'Plant').toUpperCase()}</div>
                  </div>
                  <div className="abs-fact-card">
                    <div className="abs-fact-label">Origin Status</div>
                    <div className="abs-fact-value">{String(data.facts_considered.origin_status ?? 'India').toUpperCase()}</div>
                  </div>
                  <div className="abs-fact-card">
                    <div className="abs-fact-label">Country of Origin</div>
                    <div className="abs-fact-value">{String(data.facts_considered.country_of_origin ?? 'India')}</div>
                  </div>
                  <div className="abs-fact-card">
                    <div className="abs-fact-label">IPR Stage</div>
                    <div className="abs-fact-value">{String(data.facts_considered.ipr_stage ?? 'None').replace(/_/g, ' ')}</div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Triggered Statutory Rules */}
          {data.triggered_rules && data.triggered_rules.length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--c-text)', marginBottom: '12px' }}>
                Triggered Statutory Rules
              </h3>
              {data.triggered_rules.map((rule, idx) => (
                <div key={idx} className="abs-rule-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--c-accent)' }}>{rule.rule_id}</span>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--c-primary)' }}>{rule.section_or_rule}</span>
                  </div>
                  <h4 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--c-text)', margin: '6px 0' }}>{rule.rule_name}</h4>
                  <p style={{ fontSize: '14px', color: 'var(--c-text-secondary)', lineHeight: 1.5 }}>{rule.description}</p>
                  <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--c-text-muted)', display: 'flex', gap: '16px' }}>
                    <span><strong>Authority:</strong> {rule.authority}</span>
                    {rule.required_form && <span><strong>Form:</strong> {rule.required_form}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Special Cases & Exemptions Evaluated */}
          {data.exemptions_evaluated && data.exemptions_evaluated.length > 0 && (
            <div className="card card-padded" style={{ marginTop: '20px' }}>
              <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--c-text-muted)', textTransform: 'uppercase', marginBottom: '12px' }}>
                Exemptions & Special Pathways Analysis
              </div>
              {data.exemptions_evaluated.map((ex, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '10px 0', borderBottom: i < data.exemptions_evaluated!.length - 1 ? '1px solid var(--c-border)' : 'none' }}>
                  <div>
                    <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--c-text)' }}>{ex.name}</div>
                    <div style={{ fontSize: '12px', color: 'var(--c-text-muted)' }}>{ex.source_provision}</div>
                    <div style={{ fontSize: '13px', color: 'var(--c-text-secondary)', marginTop: '4px' }}>{ex.reason}</div>
                  </div>
                  <span className={`abs-exemption-pill ${ex.is_triggered ? 'abs-exemption-triggered' : 'abs-exemption-overridden'}`}>
                    {ex.is_triggered ? 'EXEMPTION APPLIES' : 'NOT APPLICABLE / OVERRIDDEN'}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Authority Routing */}
          {data.authority_routing && (
            <div className="abs-authority-banner" style={{ marginTop: '20px' }}>
              <div style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', opacity: 0.9 }}>
                Designated Regulatory Authority
              </div>
              <div style={{ fontSize: '20px', fontWeight: 800, marginTop: '4px' }}>
                {data.authority_routing.authority_name}
              </div>
              <div style={{ fontSize: '13px', opacity: 0.9, marginTop: '4px' }}>
                Scope: {data.authority_routing.jurisdiction_scope} | Level: {data.authority_routing.authority_level}
              </div>
            </div>
          )}

          {/* Form & Document Routing */}
          {data.form_requirements && data.form_requirements.length > 0 && (
            <div className="card card-padded" style={{ marginTop: '20px' }}>
              <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--c-text-muted)', textTransform: 'uppercase', marginBottom: '12px' }}>
                Required Filing Forms & Documents
              </div>
              {data.form_requirements.map((form, i) => (
                <div key={i} style={{ padding: '12px 0', borderBottom: i < data.form_requirements!.length - 1 ? '1px solid var(--c-border)' : 'none' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--c-primary)' }}>{form.form_name}</span>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--c-accent)' }}>Fee: {form.fee}</span>
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--c-text-secondary)', marginTop: '4px' }}>{form.purpose}</p>
                  <div style={{ marginTop: '8px' }}>
                    <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--c-text-muted)' }}>Required Documents:</span>
                    <ul style={{ paddingLeft: '18px', marginTop: '4px', fontSize: '12px', color: 'var(--c-text-secondary)' }}>
                      {form.required_documents.map((doc, dIdx) => (
                        <li key={dIdx}>{doc}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Benefit Sharing Subsystem */}
          {data.benefit_sharing && data.benefit_sharing.applicable && (
            <div className="abs-benefit-box" style={{ marginTop: '20px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--c-warning)', marginBottom: '8px' }}>
                Benefit Sharing Analysis
              </h3>
              <p style={{ fontSize: '14px', color: 'var(--c-text-secondary)', lineHeight: 1.5 }}>
                <strong>Basis:</strong> {data.benefit_sharing.basis}
              </p>

              {data.benefit_sharing.turnover_inr !== undefined && data.benefit_sharing.turnover_inr !== null ? (
                <div style={{ marginTop: '12px', background: 'var(--c-surface)', padding: '12px', borderRadius: '6px', border: '1px solid var(--c-border)' }}>
                  <div style={{ fontSize: '13px', color: 'var(--c-text-secondary)' }}>
                    Turnover / Licensing Revenue: <strong>INR {data.benefit_sharing.turnover_inr.toLocaleString('en-IN')}</strong>
                  </div>
                  <div style={{ fontSize: '13px', color: 'var(--c-text-secondary)', marginTop: '4px' }}>
                    Applicable Rate / Slab: <strong>{data.benefit_sharing.rate_or_slab}</strong>
                  </div>
                  <div style={{ fontSize: '16px', fontWeight: 800, color: 'var(--c-success)', marginTop: '8px' }}>
                    Indicative Contribution: INR {data.benefit_sharing.indicative_amount_inr?.toLocaleString('en-IN')}
                  </div>
                </div>
              ) : (
                <div style={{ marginTop: '8px', fontSize: '13px', color: 'var(--c-warning)', fontStyle: 'italic' }}>
                  Turnover not provided. Click "Adaptive Intake Questionnaire" above to enter annual turnover for indicative calculation.
                </div>
              )}
              <div style={{ fontSize: '11px', color: 'var(--c-text-muted)', marginTop: '8px', fontStyle: 'italic' }}>
                {data.benefit_sharing.disclaimer}
              </div>
            </div>
          )}

          {/* Section 6 IP Filing Note */}
          {data.ip_filing_flag && data.ip_filing_note && (
            <div className="note-box" style={{ marginTop: '20px' }}>
              <span className="note-icon">!</span>
              <span>{data.ip_filing_note}</span>
            </div>
          )}

          {/* Verified Legal Evidence & Citations */}
          {data.citations && data.citations.length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--c-text)', marginBottom: '8px' }}>
                Verified Legal Evidence
              </h3>
              {data.citations.map((cit, cIdx) => (
                <div key={cIdx} className="abs-citation-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--c-primary)' }}>{cit.document_name} ({cit.doc_id})</span>
                    <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--c-success)', textTransform: 'uppercase' }}>
                      {cit.verification_status}
                    </span>
                  </div>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--c-accent)', marginTop: '4px' }}>
                    {cit.section_or_article}
                  </div>
                  <p style={{ fontSize: '13px', color: 'var(--c-text-secondary)', marginTop: '6px', fontStyle: 'italic' }}>
                    "{cit.excerpt}"
                  </p>
                  {cit.source_url && (
                    <a href={cit.source_url} target="_blank" rel="noreferrer" style={{ fontSize: '12px', color: 'var(--c-primary)', marginTop: '6px', display: 'inline-block' }}>
                      View Official Legal Corpus Source ↗
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Missing Information Banner */}
          {data.missing_information && data.missing_information.length > 0 && (
            <div className="abs-missing-box" style={{ marginTop: '20px' }}>
              <h4 style={{ fontSize: '15px', fontWeight: 700, color: 'var(--c-error)', marginBottom: '8px' }}>
                Missing Information Required to Finalize Assessment
              </h4>
              <ul style={{ listStyle: 'none', padding: 0 }}>
                {data.missing_information.map((m, mIdx) => (
                  <li key={mIdx} style={{ fontSize: '13px', color: 'var(--c-text)', marginBottom: '8px' }}>
                    <strong>{m.prompt_question}</strong> — {m.impact_description}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Human Review Escalation */}
          {data.human_escalation && data.human_escalation.human_review && (
            <div className="abs-escalation-banner" style={{ marginTop: '20px' }}>
              <h4 style={{ fontSize: '15px', fontWeight: 800, color: 'var(--c-warning)', marginBottom: '6px' }}>
                Human Review & Facilitator Escalation Recommended
              </h4>
              <p style={{ fontSize: '13px', color: 'var(--c-text)', lineHeight: 1.5 }}>
                {data.human_escalation.reason}
              </p>
              <div style={{ fontSize: '12px', color: 'var(--c-text-secondary)', marginTop: '4px' }}>
                {data.human_escalation.case_summary}
              </div>
            </div>
          )}

          {/* Next Action Steps */}
          {data.next_actions && data.next_actions.length > 0 && (
            <div className="card card-padded" style={{ marginTop: '20px' }}>
              <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--c-text-muted)', textTransform: 'uppercase', marginBottom: '12px' }}>
                Recommended Compliance Action Plan
              </div>
              <ul style={{ listStyle: 'none', padding: 0 }}>
                {data.next_actions.map((act, aIdx) => (
                  <li key={aIdx} className="checklist-item">
                    <input type="checkbox" id={`action-check-${aIdx}`} />
                    <label htmlFor={`action-check-${aIdx}`}>{act}</label>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Retained Legal Disclaimer */}
          {data.disclaimer && (
            <div className="disclaimer-box" style={{ marginTop: '24px' }}>
              {data.disclaimer}
            </div>
          )}
        </>
      )}

      <div className="nav-row" style={{ marginTop: '24px' }}>
        <Button variant="ghost" onClick={onBack}>
          Back
        </Button>
      </div>
    </div>
  )
}
