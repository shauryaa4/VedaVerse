import { useState } from 'react'
import type { Session, Screen, Jurisdiction, AskResponse } from './types'
import { createSession, classifyProduct } from './mock/mockData'
import { Landing } from './screens/Landing'
import { Jurisdiction as JurisdictionScreen } from './screens/Jurisdiction'
import { Questionnaire } from './screens/Questionnaire'
import { Classification } from './screens/Classification'
import { Query } from './screens/Query'
import { Answer } from './screens/Answer'
import { TKDLSearch } from './screens/TKDLSearch'
import { ABSHelper } from './screens/ABSHelper'
import { NavDropdown } from './components/NavDropdown'
import { HowItWorksModal } from './components/HowItWorksModal'
import { EscalationModal } from './components/EscalationModal'
import './components/ui.css'

function App() {
  const [screen, setScreen] = useState<Screen>('landing')
  const [session, setSession] = useState<Session>(() => createSession())
  const [askResponse, setAskResponse] = useState<AskResponse | null>(null)
  const [askedQuestion, setAskedQuestion] = useState('')
  const [language, setLanguage] = useState<'en' | 'hi'>('en')
  const [showHowItWorks, setShowHowItWorks] = useState(false)
  const [showEscalation, setShowEscalation] = useState(false)

  const questionnaireComplete = session.classification !== null

  const updateSession = (patch: Partial<Session>) => {
    setSession((prev) => ({ ...prev, ...patch }))
  }

  const handleJurisdiction = (j: Jurisdiction) => {
    updateSession({ jurisdiction: j })
    setScreen('questionnaire')
  }

  const handleQuestionnaireComplete = () => {
    setSession((prev) => {
      const classification = classifyProduct(prev)
      return { ...prev, classification }
    })
    setScreen('classification')
  }

  const handleAskResult = (response: AskResponse, question: string) => {
    setAskResponse(response)
    setAskedQuestion(question)
    setScreen('answer')
  }

  const resetSession = () => {
    setSession(createSession())
    setAskResponse(null)
    setAskedQuestion('')
    setScreen('landing')
  }

  const toggleLanguage = () => {
    setLanguage((prev) => (prev === 'en' ? 'hi' : 'en'))
  }

  const handleTKDL = () => {
    if (!questionnaireComplete) return
    setScreen('tkdl')
  }

  const handleABS = () => {
    if (!questionnaireComplete) return
    setScreen('abs')
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-logo" onClick={resetSession}>
          IP-SAKTI <span>Sahayak</span>
        </div>
        <div className="app-header-right">
          {language === 'hi' && <span className="app-header-meta">हिन्दी</span>}
          <NavDropdown
            language={language}
            questionnaireComplete={questionnaireComplete}
            onLanguageToggle={toggleLanguage}
            onStartOver={resetSession}
            onHowItWorks={() => setShowHowItWorks(true)}
            onEscalate={() => setShowEscalation(true)}
            onTKDL={handleTKDL}
            onABS={handleABS}
          />
        </div>
      </header>
      <main className="app-main">
        <div className="app-content">
          {screen === 'landing' && <Landing onStart={() => setScreen('jurisdiction')} />}
          {screen === 'jurisdiction' && (
            <JurisdictionScreen onSelect={handleJurisdiction} onBack={() => setScreen('landing')} />
          )}
          {screen === 'questionnaire' && (
            <Questionnaire
              session={session}
              onUpdate={updateSession}
              onComplete={handleQuestionnaireComplete}
              onBack={() => setScreen('jurisdiction')}
            />
          )}
          {screen === 'classification' && (
            <Classification
              session={session}
              onContinue={() => setScreen('query')}
              onBack={() => setScreen('questionnaire')}
              onEscalate={() => setShowEscalation(true)}
            />
          )}
          {screen === 'query' && (
            <Query
              session={session}
              onResult={handleAskResult}
              onBack={() => setScreen('classification')}
            />
          )}
          {screen === 'answer' && askResponse && (
            <Answer
              response={askResponse}
              question={askedQuestion}
              onAskAnother={() => setScreen('query')}
              onBack={() => setScreen('query')}
            />
          )}
          {screen === 'tkdl' && questionnaireComplete && (
            <TKDLSearch
              sessionId={session.session_id}
              onBack={() => setScreen('classification')}
            />
          )}
          {screen === 'tkdl' && !questionnaireComplete && (
            <div className="fade-in">
              <div className="card card-padded" style={{ marginTop: '32px', textAlign: 'center' }}>
                <p style={{ fontSize: '16px', color: 'var(--c-text-secondary)' }}>
                  Finish your product profile first
                </p>
                <p style={{ fontSize: '14px', color: 'var(--c-text-muted)', marginTop: '8px' }}>
                  Complete the questionnaire before using TKDL Search.
                </p>
              </div>
            </div>
          )}
          {screen === 'abs' && questionnaireComplete && (
            <ABSHelper
              sessionId={session.session_id}
              onBack={() => setScreen('classification')}
            />
          )}
          {screen === 'abs' && !questionnaireComplete && (
            <div className="fade-in">
              <div className="card card-padded" style={{ marginTop: '32px', textAlign: 'center' }}>
                <p style={{ fontSize: '16px', color: 'var(--c-text-secondary)' }}>
                  Finish your product profile first
                </p>
                <p style={{ fontSize: '14px', color: 'var(--c-text-muted)', marginTop: '8px' }}>
                  Complete the questionnaire before using the ABS Helper.
                </p>
              </div>
            </div>
          )}
        </div>
      </main>

      {showHowItWorks && <HowItWorksModal onClose={() => setShowHowItWorks(false)} />}
      {showEscalation && (
        <EscalationModal onClose={() => setShowEscalation(false)} />
      )}
    </div>
  )
}

export default App
