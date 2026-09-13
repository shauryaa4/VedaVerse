import { useState } from 'react';
import AppHeader from './components/AppHeader.jsx';
import EscalationCTA from './components/EscalationCTA.jsx';
import Landing from './screens/Landing.jsx';
import JurisdictionSelect from './screens/JurisdictionSelect.jsx';
import Questionnaire from './screens/Questionnaire.jsx';
import ClassificationResult from './screens/ClassificationResult.jsx';
import Workspace from './screens/Workspace.jsx';
import CitationDetailModal from './components/CitationDetailModal.jsx';
import {
  createSession,
  submitIntake,
  classify,
  askQuestion,
  getCitation,
  tkdlSearch,
  absAssess,
} from './api/client.js';

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

  // Part 3 — TKDL Search / ABS Helper tab state. Each is fetched lazily
  // (`fetched` flips true on first attempt, success or failure, so the
  // tab doesn't refetch every time it's reopened) and re-fetchable via
  // each screen's "Re-check" button.
  const [tkdl, setTkdl] = useState({ data: null, loading: false, error: null, fetched: false });
  const [abs, setAbs] = useState({ data: null, loading: false, error: null, fetched: false });

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

  const handleAskQuestion = async (question, language = 'en') => {
    setQueryLoading(true);
    setQueryError(null);
    try {
      const result = await askQuestion(pip.session_id, question, language);
      setQueryHistory((prev) => [
        ...prev,
        { id: `${Date.now()}-${prev.length}`, question, result, language },
      ]);
    } catch (err) {
      setQueryError(err.message);
    } finally {
      setQueryLoading(false);
    }
  };

  const handleFetchTkdl = async () => {
    setTkdl((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await tkdlSearch(pip.session_id);
      setTkdl({ data, loading: false, error: null, fetched: true });
    } catch (err) {
      setTkdl({ data: null, loading: false, error: err.message, fetched: true });
    }
  };

  const handleFetchAbs = async () => {
    setAbs((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await absAssess(pip.session_id);
      setAbs({ data, loading: false, error: null, fetched: true });
    } catch (err) {
      setAbs({ data: null, loading: false, error: err.message, fetched: true });
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
    setTkdl({ data: null, loading: false, error: null, fetched: false });
    setAbs({ data: null, loading: false, error: null, fetched: false });
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
          <Workspace
            pip={pip}
            classification={classification}
            queryHistory={queryHistory}
            queryLoading={queryLoading}
            queryError={queryError}
            onAsk={handleAskQuestion}
            onOpenCitation={handleOpenCitation}
            tkdl={tkdl}
            onFetchTkdl={handleFetchTkdl}
            abs={abs}
            onFetchAbs={handleFetchAbs}
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
