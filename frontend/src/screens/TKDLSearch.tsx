import { useState, useEffect } from 'react'
import type { TKDLSearchResponse } from '../types'
import { tkdlSearchAPI } from '../api'
import { Button } from '../components/Button'

interface TKDLSearchProps {
  sessionId: string
  onBack: () => void
}

export function TKDLSearch({ sessionId, onBack }: TKDLSearchProps) {
  const [data, setData] = useState<TKDLSearchResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(false)
    tkdlSearchAPI(sessionId)
      .then((res) => { if (!cancelled) { setData(res); setLoading(false) } })
      .catch(() => { if (!cancelled) { setError(true); setLoading(false) } })
    return () => { cancelled = true }
  }, [sessionId])

  const a = data?.assessment

  return (
    <div className="fade-in">
      <h1 className="section-title">TKDL Search</h1>
      <p className="section-subtitle">
        Checking your product's composition against the Traditional Knowledge Digital Library.
      </p>

      <div className="demo-banner">
        TKDL Search — DEMONSTRATION DATA. Not connected to the live Traditional Knowledge Digital Library.
      </div>

      {loading && (
        <div className="card card-padded" style={{ marginTop: '24px', textAlign: 'center', padding: '48px' }}>
          <div className="spinner" />
          <p style={{ marginTop: '16px', color: 'var(--c-text-muted)', fontSize: '14px' }}>
            Searching TKDL records...
          </p>
        </div>
      )}

      {error && (
        <div className="card card-padded error-state" style={{ marginTop: '24px' }}>
          <div style={{ fontSize: '16px', fontWeight: 600, color: 'var(--c-error)', marginBottom: '8px' }}>
            Something went wrong
          </div>
          <p style={{ fontSize: '14px', color: 'var(--c-text-secondary)' }}>
            We couldn't reach the TKDL search service. Please try again later.
          </p>
          <Button variant="primary" style={{ marginTop: '16px' }} onClick={() => {
            setLoading(true); setError(false)
            tkdlSearchAPI(sessionId).then(setData).then(() => setLoading(false)).catch(() => { setError(true); setLoading(false) })
          }}>Retry</Button>
        </div>
      )}

      {!loading && !error && a && (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '24px' }}>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--c-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Risk Level
            </span>
            <span className={`risk-badge risk-${a.risk_level}`}>
              {a.risk_level.toUpperCase()}
            </span>
          </div>

          {(a.risk_level === 'none' || !a.closest_record) ? (
            <div className="card card-padded" style={{ marginTop: '16px' }}>
              <p style={{ fontSize: '15px', color: 'var(--c-text-secondary)' }}>
                No matches in the demo dataset for this query.
              </p>
            </div>
          ) : (
            <>
              {a.closest_record && (
                <div className="card card-padded" style={{ marginTop: '16px' }}>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--c-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>
                    Closest TKDL Record
                  </div>
                  <div style={{ fontFamily: 'var(--font)', fontSize: '18px', fontWeight: 700, color: 'var(--c-text)', marginBottom: '4px' }}>
                    {a.closest_record.formulation_name}
                  </div>
                  <div style={{ fontSize: '13px', color: 'var(--c-text-muted)', marginBottom: '12px' }}>
                    {a.closest_record.source_text} &middot; {a.closest_record.formulation_type} &middot; Known for {a.closest_record.knowledge_known_since_years} years
                  </div>

                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--c-text-muted)', marginBottom: '6px' }}>Ingredients</div>
                  <ul style={{ listStyle: 'none', padding: 0, marginBottom: '12px' }}>
                    {a.closest_record.ingredients.map((ing, i) => (
                      <li key={i} style={{ fontSize: '14px', color: 'var(--c-text-secondary)', padding: '4px 0', borderBottom: '1px solid var(--c-border)' }}>
                        <strong>{ing.name}</strong>
                        {ing.scientific_name && <span style={{ color: 'var(--c-text-muted)' }}> — {ing.scientific_name}</span>}
                        {ing.traditional_name && <span style={{ color: 'var(--c-text-muted)' }}> ({ing.traditional_name})</span>}
                        {ing.part_used && <span style={{ color: 'var(--c-text-muted)' }}> — {ing.part_used}</span>}
                      </li>
                    ))}
                  </ul>

                  {a.closest_record.therapeutic_use.length > 0 && (
                    <>
                      <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--c-text-muted)', marginBottom: '6px' }}>Therapeutic Use</div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                        {a.closest_record.therapeutic_use.map((u, i) => (
                          <span key={i} className="chip" style={{ cursor: 'default' }}>{u}</span>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              )}

              <div className="card card-padded" style={{ marginTop: '16px' }}>
                <TKDLList title="What was already known" items={a.what_was_already_known} />
                <TKDLList title="What appears different" items={a.what_appears_different} />
                <TKDLList title="Potential novel features" items={a.potential_novel_features} />
              </div>

              {a.reasoning.length > 0 && (
                <div className="card card-padded" style={{ marginTop: '16px' }}>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--c-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>
                    Reasoning
                  </div>
                  <ul style={{ listStyle: 'none', padding: 0 }}>
                    {a.reasoning.map((r, i) => (
                      <li key={i} style={{ display: 'flex', gap: '12px', padding: '6px 0', fontSize: '14px', color: 'var(--c-text-secondary)', lineHeight: 1.6 }}>
                        <span style={{ color: 'var(--c-accent)', fontWeight: 700, flexShrink: 0 }}>{i + 1}.</span>
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}

          {a.disclaimer && (
            <div className="disclaimer-box" style={{ marginTop: '16px' }}>
              {a.disclaimer}
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

function TKDLList({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null
  return (
    <div style={{ marginBottom: '20px' }}>
      <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--c-text)', marginBottom: '8px' }}>{title}</div>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {items.map((item, i) => (
          <li key={i} style={{ display: 'flex', gap: '8px', padding: '4px 0', fontSize: '14px', color: 'var(--c-text-secondary)', lineHeight: 1.5 }}>
            <span style={{ color: 'var(--c-primary)', flexShrink: 0 }}>&bull;</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
