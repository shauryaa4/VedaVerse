import { useState, useRef } from 'react';
import AnswerCard from './AnswerCard.jsx';
import ErrorNotice from '../components/ErrorNotice.jsx';
import { OBJECTIVE_OPTIONS, CATEGORY_LABELS } from '../data/options.js';
import { transcribeVoice, askQuestion } from '../api/client.js';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';
import './QueryWorkspace.css';

const STARTER_QUESTIONS = {
  patentability: 'Can I patent this formulation?',
  regulatory_category: 'What regulatory category does this product fall under?',
  trademark: 'How can I protect the brand or product name?',
  prior_art: 'Has a formulation like this been done before?',
  abs_relevance: 'Do Access and Benefit-Sharing obligations apply to this product?',
  legal_pathway: 'What is the overall legal pathway for protecting this product?',
  general: 'What should I know about protecting this product?',
};

export default function QueryWorkspace({
  pip,
  classification,
  history,
  onAsk,
  onAddTurn,
  loading,
  error,
  onOpenCitation,
  onRestart,
  currentLang = 'en',
}) {
  const [chatMode, setChatMode] = useState('text'); // 'text' | 'voice'
  const [question, setQuestion] = useState('');
  
  // Voice recording & review state
  // voiceStep: 'idle' | 'recording' | 'transcribing' | 'review' | 'processing'
  const [voiceStep, setVoiceStep] = useState('idle');
  const [voiceTranscript, setVoiceTranscript] = useState('');
  const [voiceDetectedLang, setVoiceDetectedLang] = useState(currentLang);
  const [voiceError, setVoiceError] = useState(null);
  const [lastSpokenQuestion, setLastSpokenQuestion] = useState('');

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const englishRecognitionRef = useRef(null);
  const englishTranscriptRef = useRef('');
  const englishRecognitionFailedRef = useRef(false);

  const handleSubmitText = (e) => {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || loading) return;
    onAsk(trimmed, currentLang);
    setQuestion('');
  };

  const startVoiceRecording = async () => {
    setVoiceError(null);

    // The configured Bhashini ASR service handles Hindi/Indo-Aryan speech,
    // but returns a server error for English. Use the browser recognizer for
    // English microphone input; the query and answer pipeline stays the same.
    if (currentLang === 'en') {
      const BrowserRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!BrowserRecognition) {
        setVoiceError('English voice recognition is unavailable in this browser. Try Chrome or use Text Chat.');
        return;
      }

      const recognition = new BrowserRecognition();
      recognition.lang = 'en-IN';
      recognition.continuous = true;
      recognition.interimResults = true;
      englishTranscriptRef.current = '';
      englishRecognitionFailedRef.current = false;

      recognition.onresult = (event) => {
        englishTranscriptRef.current = Array.from(event.results)
          .map((result) => result[0]?.transcript || '')
          .join(' ')
          .trim();
      };
      recognition.onerror = (event) => {
        englishRecognitionFailedRef.current = true;
        setVoiceError(event.error === 'not-allowed'
          ? 'Microphone access denied. Allow microphone access and try again.'
          : `English voice recognition failed (${event.error}). Please try again.`);
        setVoiceStep('idle');
      };
      recognition.onend = () => {
        englishRecognitionRef.current = null;
        if (englishRecognitionFailedRef.current) return;
        const transcript = englishTranscriptRef.current.trim();
        if (!transcript) {
          setVoiceError('No speech was recognized. Please speak again.');
          setVoiceStep('idle');
          return;
        }
        setVoiceTranscript(transcript);
        setVoiceDetectedLang('en');
        setVoiceStep('review');
      };

      try {
        recognition.start();
        englishRecognitionRef.current = recognition;
        setVoiceStep('recording');
      } catch (err) {
        setVoiceError(`Could not start English voice recognition: ${err.message}`);
        setVoiceStep('idle');
      }
      return;
    }

    try {
      audioChunksRef.current = [];
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const mimeType = mediaRecorderRef.current.mimeType || 'audio/webm';
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        // Stop audio tracks
        stream.getTracks().forEach((track) => track.stop());
        await processAudioTranscription(audioBlob);
      };

      mediaRecorderRef.current.start();
      setVoiceStep('recording');
    } catch (err) {
      console.error('Microphone access error:', err);
      setVoiceError('Microphone access denied or unavailable.');
      setVoiceStep('idle');
    }
  };

  const stopVoiceRecording = () => {
    if (englishRecognitionRef.current && voiceStep === 'recording') {
      setVoiceStep('transcribing');
      englishRecognitionRef.current.stop();
      return;
    }
    if (mediaRecorderRef.current && voiceStep === 'recording') {
      mediaRecorderRef.current.stop();
      setVoiceStep('transcribing');
    }
  };

  const processAudioTranscription = async (audioBlob) => {
    setVoiceStep('transcribing');
    try {
      const res = await transcribeVoice(audioBlob, currentLang);
      setVoiceTranscript(res.text || '');
      setVoiceDetectedLang(res.language || currentLang);
      setVoiceStep('review');
    } catch (err) {
      console.error('ASR Transcription failed:', err);
      setVoiceError(`Voice transcription failed: ${err.message}`);
      setVoiceStep('idle');
    }
  };

  const handleConfirmVoiceQuery = async () => {
    const trimmed = voiceTranscript.trim();
    if (!trimmed) return;

    setVoiceStep('processing');
    try {
      const targetLang = voiceDetectedLang || currentLang || 'hi';
      const ragResult = await askQuestion(pip.session_id, trimmed, targetLang);
      
      const turnObj = {
        id: `${Date.now()}-${history.length}`,
        question: trimmed,
        result: ragResult,
        language: targetLang,
        isVoice: true,
      };

      if (onAddTurn) {
        onAddTurn(turnObj);
      }

      setVoiceStep('idle');
      setLastSpokenQuestion(trimmed);
      setVoiceTranscript('');
    } catch (err) {
      console.error('Voice query processing failed:', err);
      setVoiceError(`Processing failed: ${err.message}`);
      setVoiceStep('review');
    }
  };

  const handleResetVoice = () => {
    if (englishRecognitionRef.current) {
      englishRecognitionRef.current.onend = null;
      englishRecognitionRef.current.abort();
      englishRecognitionRef.current = null;
    }
    setVoiceStep('idle');
    setVoiceTranscript('');
    setVoiceError(null);
  };

  const objectives = Array.isArray(pip?.objective) ? pip.objective : [];
  const categoryLabel = CATEGORY_LABELS[classification?.category] || classification?.category || '—';
  const uiText = useTranslatedTexts([
    categoryLabel, 'Category', 'Speak Again', 'What you said:', 'Transcribing your speech…',
    'Your question (edit if needed)', 'Review or edit your spoken question...',
    'Getting your answer…', 'Retrieving and verifying an answer…',
    'Ask a question above to get a grounded, citation-backed answer.',
    'Jurisdiction', 'India', 'International', 'Based on what you told us, you might ask:',
    'Text Chat', 'Voice AI Assistant', "Ask a question about this product's IP or regulatory pathway…",
    'Asking…', 'Ask', 'Click the microphone and speak your question…', 'Tap to speak',
    'Listening... Speak now', 'Stop Recording & Send', 'Confirm & Get Answer',
    ...objectives.map((obj) => STARTER_QUESTIONS[obj] || OBJECTIVE_OPTIONS.find((o) => o.value === obj)?.label || obj),
  ], currentLang);

  return (
    <div className="workspace">
      <div className="workspace__summary card">
        <dl>
          <div>
            <dt>{uiText('Jurisdiction')}</dt>
            <dd>{pip?.jurisdiction === 'india' ? uiText('India') : pip?.jurisdiction === 'international' ? uiText('International') : '—'}</dd>
          </div>
          <div>
            <dt>{uiText('Category')}</dt>
            <dd>{uiText(categoryLabel)}</dd>
          </div>
        </dl>
      </div>

      {objectives.length > 0 && (
        <div className="workspace__objectives">
          <p className="workspace__objectives-label">{uiText('Based on what you told us, you might ask:')}</p>
          <div className="workspace__objective-chips">
            {objectives.map((obj) => {
              const starterText = STARTER_QUESTIONS[obj] || OBJECTIVE_OPTIONS.find((o) => o.value === obj)?.label || obj;
              return (
                <button
                  key={obj}
                  type="button"
                  className="workspace__objective-chip"
                  onClick={() => setQuestion(uiText(starterText))}
                  disabled={loading || voiceStep !== 'idle'}
                >
                  {uiText(starterText)}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Mode Switcher: Text Chat vs Voice AI Assistant */}
      <div className="workspace__mode-toggle">
        <button
          type="button"
          className={`workspace__mode-btn ${chatMode === 'text' ? 'workspace__mode-btn--active' : ''}`}
          onClick={() => { setChatMode('text'); handleResetVoice(); }}
        >
          💬 {uiText('Text Chat')}
        </button>
        <button
          type="button"
          className={`workspace__mode-btn ${chatMode === 'voice' ? 'workspace__mode-btn--active' : ''}`}
          onClick={() => setChatMode('voice')}
        >
          🎙️ {uiText('Voice AI Assistant')}
        </button>
      </div>

      {chatMode === 'text' ? (
        <form className="workspace__form" onSubmit={handleSubmitText}>
          <textarea
            className="workspace__input"
            placeholder={uiText("Ask a question about this product's IP or regulatory pathway…")}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            rows={3}
            disabled={loading}
          />
          <button type="submit" className="workspace__submit" disabled={loading || !question.trim()}>
            {loading ? uiText('Asking…') : uiText('Ask')}
          </button>
        </form>
      ) : (
        <div className="workspace__voice-panel card">
          {voiceError && <p className="workspace__error">{voiceError}</p>}

          {voiceStep === 'idle' && (
            <div className="workspace__voice-step">
              <p className="workspace__voice-message">
                {lastSpokenQuestion ? <>{uiText('What you said:')} {lastSpokenQuestion}</> : uiText('Click the microphone and speak your question…')}
              </p>
              <button
                type="button"
                className="workspace__mic-btn"
                onClick={startVoiceRecording}
                disabled={loading}
              >
                <span className="workspace__mic-icon">🎙️</span>
                <span className="workspace__mic-label">{lastSpokenQuestion ? uiText('Speak Again') : uiText('Tap to speak')}</span>
              </button>
            </div>
          )}

          {voiceStep === 'recording' && (
            <div className="workspace__voice-step">
              <p className="workspace__voice-message workspace__voice-message--active">
                🔴 {uiText('Listening... Speak now')}
              </p>
              <button
                type="button"
                className="workspace__mic-btn workspace__mic-btn--recording"
                onClick={stopVoiceRecording}
              >
                <span className="workspace__mic-icon">⏹️</span>
                <span className="workspace__mic-label">{uiText('Stop Recording & Send')}</span>
              </button>
            </div>
          )}

          {voiceStep === 'transcribing' && (
            <div className="workspace__voice-loading">
              <span className="workspace__spinner" />
              <p>{uiText('Transcribing your speech…')}</p>
            </div>
          )}

          {voiceStep === 'review' && (
            <div className="workspace__voice-review">
              <p className="workspace__review-title">
                {uiText('Your question (edit if needed)')}
              </p>
              <textarea
                className="workspace__review-input"
                value={voiceTranscript}
                onChange={(e) => setVoiceTranscript(e.target.value)}
                rows={3}
                placeholder={uiText('Review or edit your spoken question...')}
              />
              <div className="workspace__review-actions">
                <button
                  type="button"
                  className="workspace__btn-secondary"
                  onClick={handleResetVoice}
                >
                  🎙️ {uiText('Speak Again')}
                </button>
                <button
                  type="button"
                  className="workspace__btn-primary"
                  onClick={handleConfirmVoiceQuery}
                  disabled={!voiceTranscript.trim()}
                >
                  ✅ {uiText('Confirm & Get Answer')}
                </button>
              </div>
            </div>
          )}

          {voiceStep === 'processing' && (
            <div className="workspace__voice-loading">
              <span className="workspace__spinner" />
              <p>{uiText('Getting your answer…')}</p>
            </div>
          )}
        </div>
      )}

      <ErrorNotice error={error} onRestart={onRestart} currentLang={currentLang} />

      <div className="workspace__history">
        {history.length === 0 && !loading && voiceStep === 'idle' && (
          <p className="workspace__empty">{uiText('Ask a question above to get a grounded, citation-backed answer.')}</p>
        )}
        {(loading || voiceStep === 'processing') && (
          <p className="workspace__loading">{uiText('Retrieving and verifying an answer…')}</p>
        )}
        {history
          .slice()
          .reverse()
          .map((turn) => (
            <AnswerCard
              key={turn.id}
              turn={turn}
              onOpenCitation={onOpenCitation}
              currentLang={currentLang}
            />
          ))}
      </div>
    </div>
  );
}
