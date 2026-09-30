import { useCallback, useEffect, useRef, useState } from 'react';
import AppHeader from './components/AppHeader.jsx';
import EscalationCTA from './components/EscalationCTA.jsx';
import Landing from './screens/Landing.jsx';
import JurisdictionSelect from './screens/JurisdictionSelect.jsx';
import Questionnaire from './screens/Questionnaire.jsx';
import ClassificationResult from './screens/ClassificationResult.jsx';
import Workspace from './screens/Workspace.jsx';
import CitationDetailModal from './components/CitationDetailModal.jsx';
import WorkspaceSidebar from './components/WorkspaceSidebar.jsx';
import AccountDialog from './components/AccountDialog.jsx';
import AccountDashboard from './screens/AccountDashboard.jsx';
import DatasetExplorer from './screens/DatasetExplorer.jsx';
import {
  createSession,
  submitIntake,
  classify,
  askQuestion,
  getCitation,
  tkdlSearch,
  absAssess,
  signUpAccount,
  logInAccount,
  getCurrentAccount,
  logOutAccount,
  getSavedCases,
  getActiveCase,
  getSavedCase,
  completeCase,
  getAuthToken,
  saveAuthToken,
  clearAuthToken,
  getAccountActivity,
  saveCaseStage,
  getSavedCaseDetails,
} from './api/client.js';

export default function App() {
  const [step, setStep] = useState('landing'); // landing | jurisdiction | questionnaire | classification | workspace
  const [pip, setPip] = useState(null);
  const [classification, setClassification] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState(() => {
    try { return localStorage.getItem('ip-sakti-ui-language') || 'en'; }
    catch (_) { return 'en'; }
  });
  const [translationWarning, setTranslationWarning] = useState(false);
  const [workspaceTab, setWorkspaceTab] = useState('query');
  const [accountDialog, setAccountDialog] = useState('');
  const [accountError, setAccountError] = useState(null);
  const [accountLoading, setAccountLoading] = useState(false);
  const [accountUser, setAccountUser] = useState(null);
  const [dashboardView, setDashboardView] = useState('dashboard');
  const [savedCases, setSavedCases] = useState([]);
  const [activeCase, setActiveCase] = useState(null);
  const [casesLoading, setCasesLoading] = useState(false);
  const [casesError, setCasesError] = useState(null);
  const [activity, setActivity] = useState({ question_count: 0, abstained_count: 0, recent: [] });
  const draftSaveQueue = useRef(Promise.resolve());

  const [queryHistory, setQueryHistory] = useState([]);
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryError, setQueryError] = useState(null);
  const [citationModal, setCitationModal] = useState(null);

  const [tkdl, setTkdl] = useState({ data: null, loading: false, error: null, fetched: false });
  const [abs, setAbs] = useState({ data: null, loading: false, error: null, fetched: false });

  const asErrorState = (err) => ({ message: err.message, status: err.status });

  useEffect(() => {
    try { localStorage.setItem('ip-sakti-ui-language', selectedLanguage); } catch (_) { /* language still works for this session */ }
    setTranslationWarning(false);
  }, [selectedLanguage]);

  useEffect(() => {
    const onTranslationError = (event) => {
      if (event.detail?.language === selectedLanguage) setTranslationWarning(true);
    };
    window.addEventListener('vedaverse:translation-error', onTranslationError);
    return () => window.removeEventListener('vedaverse:translation-error', onTranslationError);
  }, [selectedLanguage]);

  const refreshSavedCases = async () => {
    setCasesLoading(true);
    setCasesError(null);
    try { setSavedCases(await getSavedCases()); }
    catch (err) { setCasesError(asErrorState(err)); }
    try { setActiveCase(await getActiveCase()); }
    catch (err) { setCasesError(asErrorState(err)); }
    try { setActivity(await getAccountActivity()); }
    catch (_) { setActivity({ question_count: 0, abstained_count: 0, recent: [] }); }
    finally { setCasesLoading(false); }
  };

  useEffect(() => {
    if (!getAuthToken()) return;
    getCurrentAccount().then(async (user) => {
      setAccountUser(user);
      setDashboardView('dashboard');
      setStep('dashboard');
      try { setSavedCases(await getSavedCases()); }
      catch (err) { setCasesError(asErrorState(err)); }
      try { setActiveCase(await getActiveCase()); }
      catch (err) { setCasesError(asErrorState(err)); }
      try { setActivity(await getAccountActivity()); } catch (_) { /* dashboard can still show saved cases */ }
    }).catch(() => clearAuthToken());
  }, []);

  const handleAccountSubmit = async (details) => {
    setAccountLoading(true);
    setAccountError(null);
    try {
      const result = accountDialog === 'signup'
        ? await signUpAccount(details)
        : await logInAccount({ email: details.email, password: details.password });
      saveAuthToken(result.access_token);
      setAccountUser(result.user);
      setDashboardView('dashboard');
      setAccountDialog('');
      setStep('dashboard');
      await refreshSavedCases();
    } catch (err) {
      setAccountError(asErrorState(err));
    } finally {
      setAccountLoading(false);
    }
  };

  const handleLogout = async () => {
    try { await logOutAccount(); } catch (_) { /* clear the local token even if the server is unavailable */ }
    clearAuthToken();
    setAccountUser(null);
    setSavedCases([]);
    setActiveCase(null);
    handleRestart();
  };

  const handleOpenSavedCase = async (sessionId) => {
    setCasesError(null);
    setCasesLoading(true);
    try {
      const savedPip = await getSavedCase(sessionId);
      const isActive = activeCase?.session_id === sessionId;
      const resumeStage = isActive ? (activeCase.stage || 'jurisdiction') : 'workspace';
      const shouldClassify = ['classification', 'workspace'].includes(resumeStage) && savedPip.jurisdiction && savedPip.protection_target;
      const result = shouldClassify ? await classify(sessionId) : savedPip.classification?.category ? savedPip.classification : null;
      setPip(savedPip);
      setClassification(result);
      const details = resumeStage === 'workspace' ? await getSavedCaseDetails(sessionId).catch(() => null) : null;
      setQueryHistory((details?.queries || []).map((query) => ({
        id: query.id,
        question: query.question,
        language: query.language || selectedLanguage,
        result: { answer_text: query.answer_text || '', used_chunks: [], abstained: query.abstained, abstain_reason: query.abstain_reason, status_notes: [] },
      })));
      setQueryError(null);
      setTkdl({ data: null, loading: false, error: null, fetched: false });
      setAbs({ data: null, loading: false, error: null, fetched: false });
      setStep(resumeStage);
      setWorkspaceTab('query');
    } catch (err) { setCasesError(asErrorState(err)); }
    finally { setCasesLoading(false); }
  };

  const handleNewCase = async () => {
    setLoading(true);
    setError(null);
    setPip(null);
    setClassification(null);
    setQueryHistory([]);
    setQueryError(null);
    setCitationModal(null);
    setTkdl({ data: null, loading: false, error: null, fetched: false });
    setAbs({ data: null, loading: false, error: null, fetched: false });
    setWorkspaceTab('query');
    try {
      const session = await createSession();
      setActiveCase(accountUser ? { session_id: session.session_id, product_name: '', updated_at: session.updated_at, stage: 'jurisdiction' } : null);
      setPip(session);
      setStep('jurisdiction');
    } catch (err) { setError(asErrorState(err)); if (accountUser) setCasesError(asErrorState(err)); setStep(accountUser ? 'dashboard' : 'landing'); }
    finally { setLoading(false); }
  };

  const handleEndCase = async () => {
    if (!pip) return;
    setLoading(true);
    setCasesError(null);
    try {
      if (accountUser) await completeCase(pip.session_id);
      setPip(null);
      setClassification(null);
      setWorkspaceTab('query');
      if (accountUser) {
        setActiveCase(null);
        setDashboardView('history');
        setStep('dashboard');
        await refreshSavedCases();
      } else {
        handleRestart();
      }
    } catch (err) {
      setCasesError(asErrorState(err));
      setQueryError(asErrorState(err));
    } finally {
      setLoading(false);
    }
  };

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
      if (accountUser) saveCaseStage(updated.session_id, 'questionnaire').catch(() => {});
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
      await draftSaveQueue.current;
      const updatedPip = await submitIntake(pip.session_id, fields);
      try { localStorage.removeItem(`ip-sakti-case-draft:${pip.session_id}`); } catch (_) { /* profile is saved on the server */ }
      setPip(updatedPip);
      const result = await classify(pip.session_id);
      setClassification(result);
      setStep('classification');
      if (accountUser) saveCaseStage(pip.session_id, 'classification').catch(() => {});
    } catch (err) {
      setError(asErrorState(err));
    } finally {
      setLoading(false);
    }
  };

  const handleDraftChange = useCallback((fields) => {
    const sessionId = pip?.session_id;
    if (!sessionId) return;
    draftSaveQueue.current = draftSaveQueue.current.then(async () => {
      const updated = await submitIntake(sessionId, fields);
      setPip((current) => current?.session_id === sessionId ? updated : current);
      if (accountUser) setActiveCase((current) => current?.session_id === sessionId ? { ...current, product_name: updated.product?.name || '', updated_at: updated.updated_at } : current);
    }).catch((err) => setError(asErrorState(err)));
  }, [pip?.session_id, accountUser?.id]);

  const handleStepSelect = async (target) => {
    if (!pip) return;
    if (step === 'questionnaire' && target !== 'questionnaire') {
      try {
        await draftSaveQueue.current;
        const rawDraft = localStorage.getItem(`ip-sakti-case-draft:${pip.session_id}`);
        if (rawDraft) {
          const updated = await submitIntake(pip.session_id, JSON.parse(rawDraft));
          setPip(updated);
          if (accountUser) setActiveCase((current) => current?.session_id === pip.session_id ? { ...current, product_name: updated.product?.name || '', updated_at: updated.updated_at } : current);
        }
      } catch (err) { setError(asErrorState(err)); return; }
    }
    if (target === 'classification' || target === 'workspace') {
      if (!pip.jurisdiction || !pip.protection_target) return;
      setLoading(true);
      try {
        const result = await classify(pip.session_id);
        setClassification(result);
        setStep(target);
        if (accountUser) saveCaseStage(pip.session_id, target).catch(() => {});
      } catch (err) { setError(asErrorState(err)); }
      finally { setLoading(false); }
      return;
    }
    setStep(target);
    if (accountUser) saveCaseStage(pip.session_id, target).catch(() => {});
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

  const handleFetchAbs = async (absFacts = null) => {
    setAbs((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await absAssess(pip.session_id, absFacts);
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
    setWorkspaceTab('query');
  };

  return (
    <div className={`app-shell${step === 'dashboard' ? ' app-shell--dashboard' : ''}${step === 'library' ? ' app-shell--library' : ''}`}>
      <AppHeader
        step={step === 'landing' || step === 'library' ? null : step}
        language={selectedLanguage}
        onRestart={accountUser ? () => { setDashboardView('dashboard'); setStep('dashboard'); refreshSavedCases(); } : handleRestart}
        onAccountAction={(action) => { setAccountError(null); setAccountDialog(action); }}
        user={accountUser}
        showDashboard={Boolean(accountUser && ['jurisdiction', 'questionnaire', 'classification', 'workspace'].includes(step))}
        onDashboard={() => { setDashboardView('dashboard'); setStep('dashboard'); refreshSavedCases(); }}
        onStepSelect={handleStepSelect}
        onLanguageChange={setSelectedLanguage}
      />

      {translationWarning && (
        <div className="app-translation-warning" role="status">
          Some text could not be translated and may still appear in English. Check the Bhashini credentials and try again.
        </div>
      )}

      <main className={`app-shell__main${['workspace', 'dashboard', 'library'].includes(step) ? ' app-shell__main--workspace' : ''}`}>
        {step === 'landing' && (
          <Landing
            onStart={handleStart}
            loading={loading}
            error={error}
            currentLang={selectedLanguage}
            onLanguageChange={setSelectedLanguage}
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
            initialPip={pip}
            onDraftChange={handleDraftChange}
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
            onContinue={() => handleStepSelect('workspace')}
            onBack={() => setStep('questionnaire')}
            currentLang={selectedLanguage}
          />
        )}

        {step === 'workspace' && (
          <>
            <WorkspaceSidebar active={workspaceTab} signedIn={!!accountUser} user={accountUser} onDashboard={() => { if (accountUser) { setDashboardView('dashboard'); setStep('dashboard'); refreshSavedCases(); } else { handleRestart(); } }} onHistory={() => { if (accountUser) { setDashboardView('history'); setStep('dashboard'); refreshSavedCases(); } else { handleRestart(); } }} onLogout={handleLogout} language={selectedLanguage} onLanguageChange={setSelectedLanguage} />
            {workspaceTab.startsWith('dataset-') ? <DatasetExplorer key={workspaceTab} dataset={workspaceTab.slice('dataset-'.length)} currentLang={selectedLanguage} onChangeDataset={(dataset) => setWorkspaceTab(`dataset-${dataset}`)} /> : <Workspace
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
              onEndCase={handleEndCase}
              canEndCase={!accountUser || activeCase?.session_id === pip?.session_id}
              currentLang={selectedLanguage}
              tab={workspaceTab}
              onTabChange={setWorkspaceTab}
            />}
          </>
        )}
        {step === 'library' && (
          <>
            <WorkspaceSidebar active="library" signedIn={!!accountUser} user={accountUser} onDashboard={() => { setDashboardView('dashboard'); setStep(accountUser ? 'dashboard' : 'landing'); if (accountUser) refreshSavedCases(); }} onHistory={() => { if (accountUser) { setDashboardView('history'); setStep('dashboard'); refreshSavedCases(); } }} onLogout={handleLogout} language={selectedLanguage} onLanguageChange={setSelectedLanguage} />
            <DatasetExplorer key={workspaceTab} dataset={workspaceTab.slice('dataset-'.length)} currentLang={selectedLanguage} onChangeDataset={(dataset) => setWorkspaceTab(`dataset-${dataset}`)} />
          </>
        )}
        {step === 'dashboard' && accountUser && (
          <>
            <WorkspaceSidebar active={dashboardView} signedIn user={accountUser} onDashboard={() => { setDashboardView('dashboard'); setStep('dashboard'); refreshSavedCases(); }} onHistory={() => { setDashboardView('history'); setStep('dashboard'); refreshSavedCases(); }} onLogout={handleLogout} language={selectedLanguage} onLanguageChange={setSelectedLanguage} />
            <AccountDashboard user={accountUser} cases={savedCases} activeCase={activeCase} activity={activity} loading={casesLoading} startingCase={loading} error={casesError} currentLang={selectedLanguage} onOpenCase={handleOpenSavedCase} onNewCase={handleNewCase} onRefresh={refreshSavedCases} onShowHistory={() => { setDashboardView('history'); refreshSavedCases(); }} onBackDashboard={() => setDashboardView('dashboard')} view={dashboardView} onNavigate={(tab) => { setWorkspaceTab(tab); setStep('library'); }} />
          </>
        )}
      </main>

      {step !== 'landing' && step !== 'dashboard' && step !== 'library' && <EscalationCTA currentLang={selectedLanguage} />}


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

      {accountDialog && <AccountDialog mode={accountDialog} loading={accountLoading} error={accountError} currentLang={selectedLanguage} onClose={() => setAccountDialog('')} onSubmit={handleAccountSubmit} />}
    </div>
  );
}
