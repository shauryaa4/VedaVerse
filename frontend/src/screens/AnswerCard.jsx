import { useEffect, useState, useRef } from 'react';
import ConfidenceBadge from '../components/ConfidenceBadge.jsx';
import { parseCitationMarkers } from '../utils/parseCitations.js';
import { generateTTS } from '../api/client.js';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';
import { translateAsync } from '../utils/translator.js';
import './AnswerCard.css';

const DEFAULT_ABSTAIN_REASON = 'Insufficient authoritative evidence in our corpus to answer this reliably. This may be outside the scope of our current legal database, or the question may require case-specific analysis. We recommend consulting a registered IP facilitator or patent agent for this query.';
const autoPlayedTurns = new Set();
let activeAnswerAudio = null;
let activeBrowserSpeech = null;

const SPEECH_LOCALES = {
  en: 'en-IN', hi: 'hi-IN', ta: 'ta-IN', bn: 'bn-IN', te: 'te-IN',
  mr: 'mr-IN', gu: 'gu-IN', kn: 'kn-IN', ml: 'ml-IN', pa: 'pa-IN',
  or: 'or-IN', ur: 'ur-IN',
};

export default function AnswerCard({ turn, onOpenCitation, currentLang = 'en' }) {
  const { question, result, language, audioBase64: initialAudio, isVoice } = turn;
  const {
    answer_text: answerText,
    abstained,
    abstain_reason: abstainReason,
    confidence,
    status_notes: statusNotes,
  } = result;

  const [audioUrl, setAudioUrl] = useState(
    initialAudio ? `data:audio/wav;base64,${initialAudio}` : null
  );
  const [loadingTts, setLoadingTts] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [autoplayBlocked, setAutoplayBlocked] = useState(false);
  const audioRef = useRef(null);
  const audioRequestRef = useRef(null);
  const browserSpeechRef = useRef(null);
  const displayNotes = (statusNotes || []).map((note) =>
    note.startsWith('No routing row matched')
      ? 'We could not match this product and question to a supported legal pathway. Please review your product details or ask a different question.'
      : note
  );

  const parts = abstained ? [] : parseCitationMarkers(answerText);
  const uiText = useTranslatedTexts([
    'Listen Voice', 'Pause', 'Loading voice…', 'Tap Listen Voice to play the answer.',
    abstainReason, DEFAULT_ABSTAIN_REASON, ...displayNotes,
  ], currentLang);

  const spokenText = abstained
    ? (abstainReason || DEFAULT_ABSTAIN_REASON)
    : parts.filter((part) => typeof part === 'string').join(' ').trim();

  const speakWithBrowser = (text, targetLang, isActive) => {
    if (!isActive() || !window.speechSynthesis || !window.SpeechSynthesisUtterance) return false;
    if (activeAnswerAudio) activeAnswerAudio.pause();
    window.speechSynthesis.cancel();
    const utterance = new window.SpeechSynthesisUtterance(text);
    utterance.lang = SPEECH_LOCALES[targetLang] || targetLang;
    const availableVoice = window.speechSynthesis.getVoices().find(
      (voice) => voice.lang?.toLowerCase() === utterance.lang.toLowerCase()
    );
    if (availableVoice) utterance.voice = availableVoice;
    utterance.onend = () => {
      if (activeBrowserSpeech === utterance) activeBrowserSpeech = null;
      setIsPlaying(false);
    };
    utterance.onerror = () => {
      if (activeBrowserSpeech === utterance) activeBrowserSpeech = null;
      setIsPlaying(false);
      setAutoplayBlocked(true);
    };
    activeBrowserSpeech = utterance;
    browserSpeechRef.current = utterance;
    window.speechSynthesis.speak(utterance);
    setIsPlaying(true);
    setAutoplayBlocked(false);
    return true;
  };

  const playAudio = async (automatic = false, isActive = () => true) => {
    if (!automatic && activeBrowserSpeech === browserSpeechRef.current && activeBrowserSpeech) {
      window.speechSynthesis.cancel();
      activeBrowserSpeech = null;
      setIsPlaying(false);
      return false;
    }
    if (!automatic && audioRef.current && !audioRef.current.paused) {
      audioRef.current.pause();
      setIsPlaying(false);
      return false;
    }

    let url = audioUrl;
    const targetLang = language || currentLang || 'en';
    const ttsText = abstained && targetLang !== 'en'
      ? await translateAsync(spokenText, targetLang)
      : spokenText;
    if (!url && spokenText) {
      setLoadingTts(true);
      try {
        if (!audioRequestRef.current) {
          audioRequestRef.current = (async () => {
            const res = await generateTTS(ttsText, targetLang);
            return res.audio_base64 ? `data:audio/wav;base64,${res.audio_base64}` : null;
          })().finally(() => { audioRequestRef.current = null; });
        }
        url = await audioRequestRef.current;
        if (isActive() && url) setAudioUrl(url);
      } catch (err) {
        console.error('TTS audio generation failed:', err);
        if (speakWithBrowser(ttsText, targetLang, isActive)) return true;
        if (isActive()) setAutoplayBlocked(true);
      } finally {
        if (isActive()) setLoadingTts(false);
      }
    }

    if (!url && speakWithBrowser(ttsText, targetLang, isActive)) return true;

    if (url && isActive()) {
      if (activeAnswerAudio && activeAnswerAudio !== audioRef.current) activeAnswerAudio.pause();
      if (!audioRef.current) {
        audioRef.current = new Audio(url);
        audioRef.current.onended = () => {
          setIsPlaying(false);
          if (activeAnswerAudio === audioRef.current) activeAnswerAudio = null;
        };
        audioRef.current.onpause = () => setIsPlaying(false);
      } else {
        audioRef.current.src = url;
      }
      try {
        await audioRef.current.play();
        if (isActive()) {
          activeAnswerAudio = audioRef.current;
          setIsPlaying(true);
          setAutoplayBlocked(false);
          return true;
        }
      } catch (err) {
        console.warn('Audio playback was blocked:', err);
        if (speakWithBrowser(ttsText, targetLang, isActive)) return true;
        if (isActive() && automatic) setAutoplayBlocked(true);
      }
    }
  };

  useEffect(() => {
    if (!isVoice || !spokenText || autoPlayedTurns.has(turn.id)) return undefined;
    let active = true;
    playAudio(true, () => active).then((played) => {
      if (active && played) {
        autoPlayedTurns.add(turn.id);
        if (autoPlayedTurns.size > 100) autoPlayedTurns.delete(autoPlayedTurns.values().next().value);
      }
    });
    return () => {
      active = false;
      audioRef.current?.pause();
      if (activeBrowserSpeech === browserSpeechRef.current && activeBrowserSpeech) {
        window.speechSynthesis.cancel();
        activeBrowserSpeech = null;
      }
    };
    // A voice turn should play once when it first appears, not on language/UI rerenders.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [turn.id, isVoice]);

  return (
    <div className="answer-card card">
      <div className="answer-card__header">
        <p className="answer-card__question">
          {isVoice ? '🎙️ ' : '💬 '} {question}
          {language && language !== 'en' && (
            <span className="answer-card__lang-tag">{language.toUpperCase()}</span>
          )}
        </p>

        {spokenText && (
          <button
            type="button"
            className={`answer-card__voice-btn ${isPlaying ? 'answer-card__voice-btn--playing' : ''}`}
            onClick={() => playAudio()}
            disabled={loadingTts}
            title={uiText('Listen Voice')}
          >
            {loadingTts ? `🔊 ${uiText('Loading voice…')}` : isPlaying ? `⏸️ ${uiText('Pause')}` : `🔊 ${uiText('Listen Voice')}`}
          </button>
        )}
      </div>

      {autoplayBlocked && <p className="answer-card__playback-hint">{uiText('Tap Listen Voice to play the answer.')}</p>}

      <div className="answer-card__meta">
        <ConfidenceBadge confidence={confidence} abstained={abstained} currentLang={currentLang} />
      </div>

      {abstained ? (
        <div className="answer-card__abstain">
          <p className="answer-card__abstain-text">
            {uiText(abstainReason || DEFAULT_ABSTAIN_REASON)}
          </p>
        </div>
      ) : (
        <p className="answer-card__text">
          {parts.map((part, i) =>
            typeof part === 'string' ? (
              <span key={i}>{part}</span>
            ) : (
              <button
                key={i}
                type="button"
                className="answer-card__citation-chip"
                onClick={() => onOpenCitation(part.docId, part.section, part.label)}
              >
                {part.label}
              </button>
            )
          )}
        </p>
      )}

      {displayNotes.length > 0 && (
        <div className="answer-card__notes">
          {displayNotes.map((note, i) => (
            <p key={i} className="answer-card__note">
              ⚠ {uiText(note)}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
