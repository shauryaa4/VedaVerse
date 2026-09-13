import type { Jurisdiction } from '../types'

interface JurisdictionProps {
  onSelect: (j: Jurisdiction) => void
  onBack: () => void
}

export function Jurisdiction({ onSelect, onBack }: JurisdictionProps) {
  return (
    <div className="fade-in">
      <h1 className="section-title">Select your jurisdiction</h1>
      <p className="section-subtitle">
        This determines which legal framework we use to classify your product and answer
        your questions.
      </p>

      <div style={{ marginTop: '32px' }}>
        <div className="option-card" onClick={() => onSelect('india')}>
          <div className="option-radio" />
          <div>
            <div className="option-label">India</div>
            <div className="option-desc">
              Patents Act 1970, Drugs &amp; Cosmetics Act 1940, Biodiversity Act 2002, FSSAI regulations
            </div>
          </div>
        </div>

        <div className="option-card" onClick={() => onSelect('international')}>
          <div className="option-radio" />
          <div>
            <div className="option-label">International</div>
            <div className="option-desc">
              TRIPS, CBD/Nagoya Protocol, WIPO traditional knowledge frameworks
            </div>
          </div>
        </div>
      </div>

      <div className="nav-row">
        <button className="btn btn-ghost" onClick={onBack}>Back</button>
      </div>
    </div>
  )
}
