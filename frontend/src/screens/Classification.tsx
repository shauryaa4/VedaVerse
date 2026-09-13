import type { Session, Category } from '../types'
import { classifyProduct } from '../mock/mockData'
import { Badge } from '../components/Badge'
import { Button } from '../components/Button'

interface ClassificationProps {
  session: Session
  onContinue: () => void
  onBack: () => void
  onEscalate: () => void
}

const categoryLabels: Record<Category, string> = {
  classical_generic: 'Classical / Generic',
  proprietary: 'Proprietary',
  new_drug: 'New Drug',
  phytopharmaceutical: 'Phytopharmaceutical',
  nutraceutical_ayurveda_aahar: 'Nutraceutical / Ayurveda-Aahar',
  cosmetic: 'Cosmetic',
  unresolved: 'Unresolved',
}

export function Classification({ session, onContinue, onBack, onEscalate }: ClassificationProps) {
  const result = session.classification ?? classifyProduct(session)
  const isUnresolved = result.category === 'unresolved' || result.confidence === 'low'

  return (
    <div className="fade-in">
      <h1 className="section-title">Classification Result</h1>
      <p className="section-subtitle">
        Based on your answers, here is the IP and regulatory category for your product.
      </p>

      <div className="card card-padded" style={{ marginTop: '32px' }}>
        {isUnresolved ? (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <span className="badge badge-low">LOW CONFIDENCE</span>
            </div>
            <div style={{ fontFamily: 'var(--font)', fontSize: '20px', fontWeight: 700, color: 'var(--c-text)', marginBottom: '8px' }}>
              We couldn't confidently classify this product from the information provided
            </div>
            <p style={{ fontSize: '14px', color: 'var(--c-text-secondary)', marginBottom: '20px' }}>
              The classification engine returned a low-confidence result. This is not an error —
              it means the answers provided don't map cleanly to a single regulatory category.
              Consider providing more detail or consulting a specialist.
            </p>

            {result.reasons.length > 0 && (
              <div style={{ marginBottom: '20px' }}>
                <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--c-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>
                  Why this was uncertain
                </div>
                <ul style={{ listStyle: 'none', padding: 0 }}>
                  {result.reasons.map((r, i) => (
                    <li key={i} style={{ display: 'flex', gap: '12px', padding: '6px 0', fontSize: '14px', color: 'var(--c-text-secondary)', lineHeight: 1.6 }}>
                      <span style={{ color: 'var(--c-accent)', fontWeight: 700, flexShrink: 0 }}>{i + 1}.</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <Button variant="primary" onClick={onEscalate}>Talk to an IP Facilitator</Button>
          </>
        ) : (
          <>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <div style={{ fontSize: '13px', color: 'var(--c-text-muted)', marginBottom: '4px' }}>Category</div>
                <div style={{ fontFamily: 'var(--font)', fontSize: '24px', fontWeight: 700, color: 'var(--c-text)' }}>
                  {categoryLabels[result.category]}
                </div>
              </div>
              <Badge level={result.confidence} />
            </div>

            <div style={{ marginTop: '24px' }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--c-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>
                Reasoning
              </div>
              <ul style={{ listStyle: 'none', padding: 0 }}>
                {result.reasons.map((r, i) => (
                  <li key={i} style={{ display: 'flex', gap: '12px', padding: '8px 0', fontSize: '15px', color: 'var(--c-text-secondary)', lineHeight: 1.6 }}>
                    <span style={{ color: 'var(--c-accent)', fontWeight: 700, flexShrink: 0 }}>{i + 1}.</span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="note-box" style={{ marginTop: '24px' }}>
              <span className="note-icon">i</span>
              <span>
                This is a deterministic rule engine, not an AI guess. The classification is based
                on fixed legal criteria mapped to your questionnaire answers.
              </span>
            </div>
          </>
        )}
      </div>

      <div className="nav-row">
        <Button variant="ghost" onClick={onBack}>Back</Button>
        {!isUnresolved && <Button variant="primary" onClick={onContinue}>Ask a Question</Button>}
      </div>
    </div>
  )
}
