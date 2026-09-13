/**
 * Parses [doc_id:section] markers out of RagResponse.answer_text.
 *
 * This is the exact format backend/rag/generation.py's prompt instructs
 * the model to emit (see `_build_prompt`'s `label = f"[{c.doc_id}:{c.section_or_article}]"`)
 * and the same shape backend/logic/citation_verification.py's
 * `_MARKER_PATTERN` parses server-side for verification. Kept in sync with
 * that regex intentionally — if the backend's marker format ever changes,
 * this is the one place on the frontend that needs to change with it.
 *
 * Returns an array of parts, in order: plain strings, and
 * { type: 'citation', docId, section, label } objects for each marker —
 * so a screen can map over the array and render citation chips as real
 * buttons instead of dangerouslySetInnerHTML.
 */
const MARKER_PATTERN = /\[([A-Za-z0-9-]+):([^\]]+)\]/g;

export function parseCitationMarkers(text) {
  if (!text) return [];

  const parts = [];
  let lastIndex = 0;
  let match;

  MARKER_PATTERN.lastIndex = 0;
  while ((match = MARKER_PATTERN.exec(text)) !== null) {
    const [full, docId, section] = match;

    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }

    parts.push({ type: 'citation', docId, section, label: `${docId} \u00a7${section}` });
    lastIndex = match.index + full.length;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts;
}
