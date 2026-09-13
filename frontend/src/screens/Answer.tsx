import { useState } from 'react'
import type { AskResponse, Citation } from '../types'
import { Badge } from '../components/Badge'
import { CitationModal } from '../components/CitationModal'
import { Button } from '../components/Button'

interface AnswerProps {
  response: AskResponse
  question: string
  onAskAnother: () => void
  onBack: () => void
}

export function Answer({ response, question, onAskAnother, onBack }: AnswerProps) {
  const [openCitation, setOpenCitation] = useState<Citation | null>(null)

  return (
    <div className="fade-in">
      <h1 className="section-title">Answer</h1>
      <p className="section-subtitle" style={{ fontStyle: 'italic' }}>
        "{question}"
      </p>

      <div className="card card-padded" style={{ marginTop: '32px' }}>
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
          <Badge level={response.confidence} />
        </div>

        {response.abstained ? (
          <div>
            <p style={{ fontSize: '15px', color: 'var(--c-text-secondary)', lineHeight: 1.7, marginBottom: '24px' }}>
              {response.answer}
            </p>
            <Button variant="primary">Consult an IP facilitator</Button>
          </div>
        ) : (
          <div>
            <p style={{ fontSize: '15px', color: 'var(--c-text)', lineHeight: 1.7, marginBottom: '20px' }}>
              {response.answer}
            </p>

            {response.citations.length > 0 && (
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--c-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '10px' }}>
                  Citations
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {response.citations.map((c, i) => (
                    <button
                      key={i}
                      className="citation-chip"
                      onClick={() => setOpenCitation(c)}
                    >
                      [{c.doc_id}, {c.section}]
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* EscalationCTA component mounts here — built separately */}
      <div id="escalation-cta-slot" />

      <div className="nav-row">
        <Button variant="ghost" onClick={onBack}>Back</Button>
        <Button variant="primary" onClick={onAskAnother}>Ask another question</Button>
      </div>

      {openCitation && (
        <CitationModal citation={openCitation} onClose={() => setOpenCitation(null)} />
      )}
    </div>
  )
}
