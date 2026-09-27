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

export default function App() {
  const [step, setStep] = useState('landing'); // landing | jurisdiction | questionnaire | classification | workspace
  const [pip, setPip] = useState(null);
  const [classification, setClassification] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState('en');

  const [queryHistory, setQueryHistory] = useState([]);
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryError, setQueryError] = useState(null);
  const [citationModal, setCitationModal] = useState(null);

  const [tkdl, setTkdl] = useState({ data: null, loading: false, error: null, fetched: false });
  const [abs, setAbs] = useState({ data: null, loading: false, error: null, fetched: false });

  const asErrorState = (err) => ({ message: err.message, status: err.status });

  const handleStart = async () => {
    setLoading(true);
    setError(null);
    try {
      const session = await createSession();
      setPip(session);
      setStep('jurisdiction');
    } catch (err) {
      setError(asErrorState(err));
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
      setError(asErrorState(err));
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
      setError(asErrorState(err));
    } finally {
      setLoading(false);
    }
  };

  const handleAskQuestion = async (question, language = selectedLanguage) => {
    setQueryLoading(true);
    setQueryError(null);
    try {
      const result = await askQuestion(pip.session_id, question, language);
      setQueryHistory((prev) => [
        ...prev,
        { id: `${Date.now()}-${prev.length}`, question, result, language },
      ]);
    } catch (err) {
      setQueryError(asErrorState(err));
    } finally {
      setQueryLoading(false);
    }
  };

  const handleAddTurn = (turnObj) => {
    setQueryHistory((prev) => [...prev, turnObj]);
  };

  const handleFetchTkdl = async () => {
    setTkdl((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await tkdlSearch(pip.session_id);
      setTkdl({ data, loading: false, error: null, fetched: true });
    } catch (err) {
      setTkdl({ data: null, loading: false, error: asErrorState(err), fetched: true });
    }
  };

  const handleFetchAbs = async () => {
    setAbs((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await absAssess(pip.session_id);
      setAbs({ data, loading: false, error: null, fetched: true });
    } catch (err) {
      setAbs({ data: null, loading: false, error: asErrorState(err), fetched: true });
    }
  };

  const handleOpenCitation = async (docId, section, label) => {
    setCitationModal({ label, loading: true, error: null, detail: null });
    try {
      const detail = await getCitation(pip.session_id, docId, section);
      setCitationModal({ label, loading: false, error: null, detail });
    } catch (err) {
      setCitationModal({ label, loading: false, error: asErrorState(err), detail: null });
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
        language={selectedLanguage}
        onLanguageChange={setSelectedLanguage}
        onRestart={handleRestart}
      />

      <main className="app-shell__main">
        {step === 'landing' && (
          <Landing
            onStart={handleStart}
            loading={loading}
            error={error}
            currentLang={selectedLanguage}
          />
        )}

        {step === 'jurisdiction' && (
          <JurisdictionSelect
            onSelect={handleJurisdictionSelect}
            loading={loading}
            error={error}
            onRestart={handleRestart}
            currentLang={selectedLanguage}
          />
        )}

        {step === 'questionnaire' && (
          <Questionnaire
            onSubmit={handleQuestionnaireSubmit}
            loading={loading}
            error={error}
            onRestart={handleRestart}
            currentLang={selectedLanguage}
          />
        )}

        {step === 'classification' && (
          <ClassificationResult
            classification={classification}
            onContinue={() => setStep('workspace')}
            onBack={() => setStep('questionnaire')}
            currentLang={selectedLanguage}
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
            onAddTurn={handleAddTurn}
            onOpenCitation={handleOpenCitation}
            tkdl={tkdl}
            onFetchTkdl={handleFetchTkdl}
            abs={abs}
            onFetchAbs={handleFetchAbs}
            onRestart={handleRestart}
            currentLang={selectedLanguage}
          />
        )}
      </main>

      {step !== 'landing' && <EscalationCTA currentLang={selectedLanguage} />}


      {citationModal && (
        <CitationDetailModal
          label={citationModal.label}
          loading={citationModal.loading}
          error={citationModal.error}
          detail={citationModal.detail}
          onClose={handleCloseCitation}
          onRestart={handleRestart}
          currentLang={selectedLanguage}
        />
      )}
    </div>
  );
}
