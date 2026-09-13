import { Button } from '../components/Button'

interface LandingProps {
  onStart: () => void
}

export function Landing({ onStart }: LandingProps) {
  return (
    <div className="fade-in">
      <h1 className="section-title">IP-SAKTI Sahayak</h1>
      <p className="section-subtitle">
        A guided tool for Ayurveda product makers to navigate the intellectual property
        and regulatory landscape.
      </p>

      <div className="card card-padded" style={{ marginTop: '32px' }}>
        <h2 style={{ fontFamily: 'var(--font)', fontSize: '18px', marginBottom: '16px', color: 'var(--c-text)' }}>
          The problem
        </h2>
        <p style={{ fontSize: '15px', color: 'var(--c-text-secondary)', lineHeight: 1.7, marginBottom: '16px' }}>
          Ayurveda products sit at the intersection of multiple, often overlapping legal
          frameworks. Determining which regime applies is rarely straightforward:
        </p>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          {[
            { area: 'Patent Law', desc: 'Patents Act, 1970 — §3(p) excludes traditional knowledge, but novel combinations may qualify.' },
            { area: 'Drug Regulation', desc: 'Drugs & Cosmetics Act, 1940 — ASU drug licensing, proprietary vs. classical categories.' },
            { area: 'Food Law', desc: 'FSSAI regulations — Ayurveda-Aahar health supplements vs. therapeutic drugs.' },
            { area: 'Biodiversity Law', desc: 'Biodiversity Act, 2002 — access and benefit-sharing for biological resources.' },
            { area: 'Traditional Knowledge', desc: 'TKDL and prior-art defenses — protecting and challenging claims on classical formulations.' },
          ].map((item) => (
            <li key={item.area} style={{ display: 'flex', gap: '12px', padding: '10px 0', borderBottom: '1px solid var(--c-border)' }}>
              <span style={{ fontWeight: 600, color: 'var(--c-primary)', minWidth: '160px', flexShrink: 0, fontSize: '14px' }}>
                {item.area}
              </span>
              <span style={{ fontSize: '14px', color: 'var(--c-text-secondary)' }}>{item.desc}</span>
            </li>
          ))}
        </ul>
      </div>

      <div style={{ marginTop: '32px' }}>
        <Button variant="primary" size="lg" onClick={onStart}>
          Get Started
        </Button>
      </div>

      <p style={{ marginTop: '16px', fontSize: '13px', color: 'var(--c-text-muted)' }}>
        Answer a short questionnaire to classify your product, then ask grounded legal
        questions with citations.
      </p>
    </div>
  )
}
