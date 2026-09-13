import { useState } from 'react'
import type { Session, Objective } from '../types'
import { askQuestion } from '../mock/mockData'
import { Button } from '../components/Button'
import type { AskResponse } from '../types'

interface QueryProps {
  session: Session
  onResult: (response: AskResponse, question: string) => void
  onBack: () => void
}

const objectiveLabels: Record<Objective, string> = {
  patentability: 'Patentability',
  regulatory_category: 'Regulatory category',
  trademark: 'Trademark',
  prior_art: 'Prior art',
  abs_relevance: 'ABS relevance',
  legal_pathway: 'Legal pathway',
  general: 'General',
}

export function Query({ session, onResult, onBack }: QueryProps) {
  const [question, setQuestion] = useState('')
  const [objectives, setObjectives] = useState<Objective[]>(session.objective)
  const [loading, setLoading] = useState(false)

  const toggleObjective = (o: Objective) => {
    setObjectives((prev) => prev.includes(o) ? prev.filter((x) => x !== o) : [...prev, o])
  }

  const submit = async () => {
    if (!question.trim()) return
    setLoading(true)
    const res = await askQuestion(question, objectives)
    setLoading(false)
    onResult(res, question)
  }

  return (
    <div className="fade-in">
      <h1 className="section-title">Ask a question</h1>
      <p className="section-subtitle">
        Ask about your product's IP or regulatory status. Adjust the focus areas to guide the answer.
      </p>

      <div className="card card-padded" style={{ marginTop: '32px' }}>
        <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--c-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '10px' }}>
          Focus areas
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '20px' }}>
          {(Object.keys(objectiveLabels) as Objective[]).map((o) => (
            <div
              key={o}
              className={`chip ${objectives.includes(o) ? 'active' : ''}`}
              onClick={() => toggleObjective(o)}
            >
              {objectiveLabels[o]}
            </div>
          ))}
        </div>

        <label style={{ fontSize: '13px', fontWeight: 600, color: 'var(--c-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '10px', display: 'block' }}>
          Your question
        </label>
        <textarea
          className="input"
          placeholder="Ask a question about your product's IP or regulatory status..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit() }}
        />

        <div className="nav-row">
          <Button variant="ghost" onClick={onBack}>Back</Button>
          <Button variant="primary" onClick={submit} disabled={!question.trim() || loading}>
            {loading ? 'Searching...' : 'Submit'}
          </Button>
        </div>
      </div>
    </div>
  )
}
