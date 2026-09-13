import { useState, useRef, useEffect } from 'react'

interface NavDropdownProps {
  language: 'en' | 'hi'
  questionnaireComplete: boolean
  onLanguageToggle: () => void
  onStartOver: () => void
  onHowItWorks: () => void
  onEscalate: () => void
  onTKDL: () => void
  onABS: () => void
}

export function NavDropdown({
  language,
  questionnaireComplete,
  onLanguageToggle,
  onStartOver,
  onHowItWorks,
  onEscalate,
  onTKDL,
  onABS,
}: NavDropdownProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handle = (fn: () => void) => {
    fn()
    setOpen(false)
  }

  return (
    <div className="nav-dropdown" ref={ref}>
      <button className="nav-trigger" onClick={() => setOpen(!open)} aria-label="Menu">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <line x1="2" y1="4" x2="16" y2="4" />
          <line x1="2" y1="9" x2="16" y2="9" />
          <line x1="2" y1="14" x2="16" y2="14" />
        </svg>
      </button>
      {open && (
        <div className="nav-menu">
          <button className="nav-item" onClick={() => handle(onStartOver)}>
            Start Over
          </button>
          <button className="nav-item" onClick={() => handle(onHowItWorks)}>
            How this works
          </button>
          {questionnaireComplete && (
            <>
              <div className="nav-divider" />
              <button className="nav-item" onClick={() => handle(onTKDL)}>
                TKDL Search
              </button>
              <button className="nav-item" onClick={() => handle(onABS)}>
                ABS Helper
              </button>
            </>
          )}
          <div className="nav-divider" />
          {/* Hindi/Bhashini toggle — backend not wired yet, do not build against this until /query returns a translation flag */}
          <button className="nav-item nav-item-row" onClick={() => handle(onLanguageToggle)}>
            <span>Language</span>
            <span className="nav-lang-toggle">
              {language === 'en' ? 'English' : 'हिन्दी'}
            </span>
          </button>
          <div className="nav-divider" />
          <button className="nav-item nav-item-accent" onClick={() => handle(onEscalate)}>
            Talk to an IP Facilitator
          </button>
        </div>
      )}
    </div>
  )
}
