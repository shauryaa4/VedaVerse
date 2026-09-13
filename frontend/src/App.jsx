import { useState } from 'react';
import AppHeader from './components/AppHeader.jsx';
import EscalationCTA from './components/EscalationCTA.jsx';
import Landing from './screens/Landing.jsx';
import JurisdictionSelect from './screens/JurisdictionSelect.jsx';
import Questionnaire from './screens/Questionnaire.jsx';
import ClassificationResult from './screens/ClassificationResult.jsx';
import WorkspacePlaceholder from './screens/WorkspacePlaceholder.jsx';
import { createSession, submitIntake, classify } from './api/client.js';

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

  const handleRestart = () => {
    setStep('landing');
    setPip(null);
    setClassification(null);
    setError(null);
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
          <WorkspacePlaceholder
            pip={pip}
            classification={classification}
            onBack={() => setStep('classification')}
          />
        )}
      </main>

      {step !== 'landing' && <EscalationCTA />}
    </div>
  );
}
