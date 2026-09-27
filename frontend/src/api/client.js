/**
 * Thin wrapper around the real backend (build spec §13 / the actual routes
 * in backend/routes/*.py). Every function here maps 1:1 to a real endpoint —
 * nothing in this file talks to mock data.
 *
 * Base URL comes from VITE_API_BASE (see .env.example). Falls back to the
 * local dev default so `npm run dev` works out of the box against a
 * locally-running `uvicorn backend.main:app --reload --port 8000`.
 */

const BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';
const AUTH_TOKEN_KEY = 'ip-sakti-auth-token';

export function getAuthToken() { return localStorage.getItem(AUTH_TOKEN_KEY); }
export function saveAuthToken(token) { localStorage.setItem(AUTH_TOKEN_KEY, token); }
export function clearAuthToken() { localStorage.removeItem(AUTH_TOKEN_KEY); }

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(`${BASE}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(getAuthToken() ? { Authorization: `Bearer ${getAuthToken()}` } : {}),
        ...(options.headers || {}),
      },
      ...options,
    });
  } catch (networkErr) {
    throw new Error(
      `Could not reach the backend at ${BASE}${path}. Is uvicorn running? (${networkErr.message})`
    );
  }

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch (_) {
      /* response wasn't JSON — fall back to statusText */
    }
    const err = new Error(detail || `Request to ${path} failed with ${res.status}`);
    err.status = res.status;
    throw err;
  }

  if (res.status === 204) return null;

  return res.json();
}

async function requestFormData(path, formData, fallbackMessage) {
  let res;
  try {
    res = await fetch(`${BASE}${path}`, {
      method: 'POST',
      headers: getAuthToken() ? { Authorization: `Bearer ${getAuthToken()}` } : {},
      body: formData,
    });
  } catch (networkErr) {
    throw new Error(
      `Could not reach the backend at ${BASE}${path}. Is the backend running? (${networkErr.message})`
    );
  }

  if (!res.ok) {
    let detail = res.statusText || fallbackMessage;
    try {
      const body = await res.json();
      detail = body.detail || JSON.stringify(body);
    } catch (_) {
      /* response wasn't JSON — fall back to statusText */
    }
    const err = new Error(detail || fallbackMessage);
    err.status = res.status;
    throw err;
  }

  return res.json();
}

export function signUpAccount(details) {
  return request('/auth/signup', { method: 'POST', body: JSON.stringify(details) });
}

export function logInAccount(credentials) {
  return request('/auth/login', { method: 'POST', body: JSON.stringify(credentials) });
}

export function getCurrentAccount() { return request('/auth/me'); }

export function logOutAccount() {
  return request('/auth/logout', { method: 'POST', body: '{}' });
}

export function getSavedCases() { return request('/auth/cases'); }
export function getActiveCase() { return request('/auth/active-case'); }
export function completeCase(sessionId) {
  return request(`/auth/cases/${encodeURIComponent(sessionId)}/complete`, { method: 'POST', body: '{}' });
}

export function getSavedCase(sessionId) {
  return request(`/auth/cases/${encodeURIComponent(sessionId)}`);
}

export function getSavedCaseDetails(sessionId) {
  return request(`/auth/cases/${encodeURIComponent(sessionId)}/details`);
}

export function deleteSavedCase(sessionId) {
  return request(`/auth/cases/${encodeURIComponent(sessionId)}`, { method: 'DELETE' });
}

export function saveCaseStage(sessionId, stage) {
  return request(`/auth/cases/${encodeURIComponent(sessionId)}/stage`, { method: 'PATCH', body: JSON.stringify({ stage }) });
}

export function getAccountActivity() { return request('/auth/activity'); }

export function searchDataset(dataset, query = '', limit = 20, offset = 0, jurisdiction = 'all') {
  const params = new URLSearchParams({ q: query, limit: String(limit), offset: String(offset) });
  if (dataset === 'legal' && jurisdiction !== 'all') params.set('jurisdiction', jurisdiction);
  return request(`/datasets/${dataset}?${params}`);
}

/** POST /session -> full (empty) ProductIntelligenceProfile, includes session_id */
export function createSession() {
  return request('/session', { method: 'POST', body: JSON.stringify({}) });
}

/**
 * POST /intake -> updated ProductIntelligenceProfile.
 * `fields` is any subset of the flattened intake fields (see backend
 * routes/intake.py IntakeRequest) — jurisdiction, protection_target,
 * objective, product_name, composition, intended_use, classical_basis,
 * classical_reference, novelty, ingredient_sources, biological_origin_known,
 * biological_origin_region, development_status.
 */
export function submitIntake(sessionId, fields) {
  return request('/intake', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, ...fields }),
  });
}

/** POST /classify -> {category, reasons[], confidence, unresolved_flags[]} */
export function classify(sessionId) {
  return request('/classify', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId }),
  });
}

/**
 * POST /query -> RagResponse: {answer_text, used_chunks[], abstained,
 * abstain_reason, confidence, confidence_reason, status_notes[], ...}
 * `language` is "en" | "hi" (backend.logic.language._SUPPORTED_LANGUAGES).
 */
export function askQuestion(sessionId, question, language = 'en') {
  return request('/query', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, question, language }),
  });
}

/** POST /tkdl/search -> {assessment, matches[]} from the offline source-derived archive */
export function tkdlSearch(sessionId) {
  return request('/tkdl/search', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId }),
  });
}

/** POST /abs/assess -> ABSAssessment */
export function absAssess(sessionId) {
  return request('/abs/assess', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId }),
  });
}

/** GET /citation/{doc_id}/{section}?session_id=... -> {doc_name, section, excerpt_text, verified} */
export function getCitation(sessionId, docId, section) {
  const params = new URLSearchParams({ session_id: sessionId });
  return request(`/citation/${encodeURIComponent(docId)}/${encodeURIComponent(section)}?${params}`);
}

/** GET /health -> {status: "ok"} */
export function checkHealth() {
  return request('/health');
}

/** POST /bhashini/translate -> {original_text, translated_text, source_lang, target_lang} */
export function translateText(text, targetLang, sourceLang = null) {
  return request('/bhashini/translate', {
    method: 'POST',
    body: JSON.stringify({ text, lang: targetLang, source_lang: sourceLang }),
  });
}

/** POST /bhashini/translate_batch -> {translations: string[]} */
export function translateBatch(texts, targetLang, sourceLang = 'en') {
  return request('/bhashini/translate_batch', {
    method: 'POST',
    body: JSON.stringify({ texts, target_lang: targetLang, source_lang: sourceLang }),
  });
}

/** POST /voice/transcribe -> {text, language} */
export async function transcribeVoice(audioFile, language = null) {
  const formData = new FormData();
  formData.append('audio', audioFile);
  if (language) formData.append('language', language);

  return requestFormData('/voice/transcribe', formData, 'Voice transcription failed.');
}

/** POST /voice/tts -> {audio_base64, language} */
export function generateTTS(text, language = 'hi') {
  return request('/voice/tts', {
    method: 'POST',
    body: JSON.stringify({ text, language }),
  });
}

/** POST /voice/chat -> {transcript, detected_language, english_question, result, audio_base64} */
export async function sendVoiceChat(sessionId, audioBlob, language = null) {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'speech.wav');
  formData.append('session_id', sessionId);
  if (language) formData.append('language', language);

  return requestFormData('/voice/chat', formData, 'Voice chat processing failed.');
}

