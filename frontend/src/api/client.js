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

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(`${BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
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

  return res.json();
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

/** POST /tkdl/search -> {assessment, matches[], mock: true} */
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
