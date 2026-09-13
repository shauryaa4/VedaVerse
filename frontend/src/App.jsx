import { useState } from 'react';
import AppHeader from './components/AppHeader.jsx';
import EscalationCTA from './components/EscalationCTA.jsx';
import Landing from './screens/Landing.jsx';
import JurisdictionSelect from './screens/JurisdictionSelect.jsx';
import Questionnaire from './screens/Questionnaire.jsx';
import ClassificationResult from './screens/ClassificationResult.jsx';
import QueryWorkspace from './screens/QueryWorkspace.jsx';
import CitationDetailModal from './components/CitationDetailModal.jsx';
import { createSession, submitIntake, classify, askQuestion, getCitation } from './api/client.js';

/**
 * Owns all real session/PIP state and every backend call in the wizard.
 * Screens are presentation + local form state only — they call the
 * on* callbacks here, which are the only things that touch api/client.js.
 * This keeps the wiring in one place, which matters once Part 2 adds the
 * query/answer loop and Part 3 adds TKDL/ABS on top of the same pip state.
 */
export default function App() {
  const [step, setStep] = useState('landing'); // landing | jurisdiction | questionnaire | classification | workspace
  const [pip, setPip] = useState(null);
  const [classification, setClassification] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Part 2 — query/answer workspace state. `queryHistory` holds every
  // {id, question, result} turn from POST /query this session, newest
  // last (QueryWorkspace reverses it for display). `citationModal` is
  // null when closed, or {label, loading, error, detail} while a
  // citation chip's GET /citation/{doc_id}/{section} request is in
  // flight or has resolved.
  const [queryHistory, setQueryHistory] = useState([]);
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryError, setQueryError] = useState(null);
  const [citationModal, setCitationModal] = useState(null);

  const handleStart = async () => {
    setLoading(true);
    setError(null);
    try {
      const session = await createSession();
      setPip(session);
      setStep('jurisdiction');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleJurisdictionSelect = async (jurisdiction) => {
    setLoading(true);
    setError(null);
    try {
      const updated = await submitIntake(pip.session_id, { jurisdiction });
      setPip(updated);
      setStep('questionnaire');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleQuestionnaireSubmit = async (fields) => {
    setLoading(true);
    setError(null);
    try {
      const updatedPip = await submitIntake(pip.session_id, fields);
      setPip(updatedPip);
      const result = await classify(pip.session_id);
      setClassification(result);
      setStep('classification');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAskQuestion = async (question) => {
    setQueryLoading(true);
    setQueryError(null);
    try {
      const result = await askQuestion(pip.session_id, question);
      setQueryHistory((prev) => [...prev, { id: `${Date.now()}-${prev.length}`, question, result }]);
    } catch (err) {
      setQueryError(err.message);
    } finally {
      setQueryLoading(false);
    }
  };

  const handleOpenCitation = async (docId, section, label) => {
    setCitationModal({ label, loading: true, error: null, detail: null });
    try {
      const detail = await getCitation(pip.session_id, docId, section);
      setCitationModal({ label, loading: false, error: null, detail });
    } catch (err) {
      setCitationModal({ label, loading: false, error: err.message, detail: null });
    }
  };

  const handleCloseCitation = () => setCitationModal(null);

  const handleRestart = () => {
    setStep('landing');
    setPip(null);
    setClassification(null);
    setError(null);
    setQueryHistory([]);
    setQueryError(null);
    setCitationModal(null);
  };

  return (
    <div className="app-shell">
      <AppHeader
        step={step === 'landing' ? null : step}
        jurisdiction={pip?.jurisdiction}
        onRestart={handleRestart}
      />

      <main className="app-shell__main">
        {step === 'landing' && (
          <Landing onStart={handleStart} loading={loading} error={error} />
        )}

        {step === 'jurisdiction' && (
          <JurisdictionSelect
            onSelect={handleJurisdictionSelect}
            loading={loading}
            error={error}
          />
        )}

        {step === 'questionnaire' && (
          <Questionnaire onSubmit={handleQuestionnaireSubmit} loading={loading} error={error} />
        )}

        {step === 'classification' && (
          <ClassificationResult
            classification={classification}
            onContinue={() => setStep('workspace')}
            onBack={() => setStep('questionnaire')}
          />
        )}

        {step === 'workspace' && (
          <QueryWorkspace
            pip={pip}
            classification={classification}
            history={queryHistory}
            onAsk={handleAskQuestion}
            loading={queryLoading}
            error={queryError}
            onOpenCitation={handleOpenCitation}
          />
        )}
      </main>

      {step !== 'landing' && <EscalationCTA />}

      {citationModal && (
        <CitationDetailModal
          label={citationModal.label}
          loading={citationModal.loading}
          error={citationModal.error}
          detail={citationModal.detail}
          onClose={handleCloseCitation}
        />
      )}
    </div>
  );
}
