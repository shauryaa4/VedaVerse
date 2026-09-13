import { useState, useEffect } from 'react'
import type { ABSAssessResponse } from '../types'
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

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(false)
    absAssessAPI(sessionId)
      .then((res) => { if (!cancelled) { setData(res); setLoading(false) } })
      .catch(() => { if (!cancelled) { setError(true); setLoading(false) } })
    return () => { cancelled = true }
  }, [sessionId])

  return (
    <div className="fade-in">
      <h1 className="section-title">ABS Helper</h1>
      <p className="section-subtitle">
        Assessing whether Access and Benefit Sharing provisions apply to your product.
      </p>

      <div className="demo-banner">
        ABS-aware decision support — not a live filing status check. No NBA/State Biodiversity Board integration.
      </div>

      {loading && (
        <div className="card card-padded" style={{ marginTop: '24px', textAlign: 'center', padding: '48px' }}>
          <div className="spinner" />
          <p style={{ marginTop: '16px', color: 'var(--c-text-muted)', fontSize: '14px' }}>
            Assessing ABS relevance...
          </p>
        </div>
      )}

      {error && (
        <div className="card card-padded error-state" style={{ marginTop: '24px' }}>
          <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--c-error)', marginBottom: '8px' }}>
            Something went wrong
          </div>
          <p style={{ fontSize: '14px', color: 'var(--c-text-secondary)' }}>
            We couldn't reach the ABS assessment service. Please try again later.
          </p>
          <Button variant="primary" style={{ marginTop: '16px' }} onClick={() => {
            setLoading(true); setError(false)
            absAssessAPI(sessionId).then(setData).then(() => setLoading(false)).catch(() => { setError(true); setLoading(false) })
          }}>Retry</Button>
        </div>
      )}

      {!loading && !error && data && (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '24px' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--c-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              ABS Relevance
            </span>
            <span className={`abs-badge abs-${data.relevance}`}>
              {data.relevance.replace('_', ' ').toUpperCase()}
            </span>
          </div>

          {data.relevance === 'not_applicable' ? (
            <div className="card card-padded" style={{ marginTop: '16px' }}>
              <p style={{ fontSize: '15px', color: 'var(--c-text-secondary)' }}>
                ABS doesn't appear to apply based on your product profile.
              </p>
            </div>
          ) : (
            <>
              {data.reasoning.length > 0 && (
                <div className="card card-padded" style={{ marginTop: '16px' }}>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--c-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>
                    Reasoning
                  </div>
                  <ul style={{ listStyle: 'none', padding: 0 }}>
                    {data.reasoning.map((r, i) => (
                      <li key={i} style={{ display: 'flex', gap: '12px', padding: '6px 0', fontSize: '14px', color: 'var(--c-text-secondary)', lineHeight: 1.6 }}>
                        <span style={{ color: 'var(--c-accent)', fontWeight: 700, flexShrink: 0 }}>{i + 1}.</span>
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {data.applicable_authority_guidance.length > 0 && (
                <div className="card card-padded" style={{ marginTop: '16px' }}>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--c-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>
                    Authority Guidance — Checklist
                  </div>
                  <ul style={{ listStyle: 'none', padding: 0 }}>
                    {data.applicable_authority_guidance.map((g, i) => (
                      <li key={i} className="checklist-item">
                        <input type="checkbox" id={`abs-check-${i}`} />
                        <label htmlFor={`abs-check-${i}`}>{g}</label>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {data.ip_filing_flag && data.ip_filing_note && (
                <div className="note-box" style={{ marginTop: '16px' }}>
                  <span className="note-icon">!</span>
                  <span>{data.ip_filing_note}</span>
                </div>
              )}
            </>
          )}

          {data.disclaimer && (
            <div className="disclaimer-box" style={{ marginTop: '16px' }}>
              {data.disclaimer}
            </div>
          )}
        </>
      )}

      <div className="nav-row">
        <Button variant="ghost" onClick={onBack}>Back</Button>
      </div>
    </div>
  )
}
