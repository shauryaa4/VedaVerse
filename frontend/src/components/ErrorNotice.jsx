import './ErrorNotice.css';

/**
 * Part 4 — reusable error banner with recovery actions.
 *
 * Build spec §19 names "Live demo Wi-Fi/API failure" as the single most
 * likely live-demo failure. In practice the concrete version of that for
 * this app is: session state lives only in-memory on the backend
 * (backend/services/citation_cache.py, the PIP store, etc. — nothing is
 * persisted to a real DB per the repo notes), so a backend restart, a long
 * idle gap, or a redeploy mid-demo invalidates every session_id currently
 * held by the frontend. Every subsequent call then fails with the
 * backend's exact message: "Unknown session_id. Call POST /session first."
 * (see backend/routes/*.py's session lookup).
 *
 * Rather than surfacing that raw string as an unrecoverable dead end, this
 * component detects that specific failure mode (by HTTP status when
 * available, falling back to matching the known message shape) and shows
 * a one-click "Start a new session" action instead of just an error line.
 * For every other error it falls back to a plain message, with an
 * optional "Try again" action the caller can wire to whatever retry makes
 * sense for that screen.
 *
 * Accepts `error` as either a plain string (existing call sites) or an
 * {message, status} object (Part 4 onward — see api/client.js, which
 * already sets err.status on every thrown error; App.jsx now preserves it
 * instead of discarding it with err.message alone).
 */
function getMessage(error) {
  if (!error) return '';
  return typeof error === 'string' ? error : error.message || '';
}

function getStatus(error) {
  if (!error || typeof error === 'string') return undefined;
  return error.status;
}

function isSessionLost(error) {
  const status = getStatus(error);
  if (status === 404) return true;
  const message = getMessage(error);
  return /session[_\s]?id/i.test(message) && /unknown|not found|expired|call post/i.test(message);
}

function isNetworkError(error) {
  return /could not reach the backend/i.test(getMessage(error));
}

export default function ErrorNotice({ error, onRetry, onRestart, retryLabel = 'Try again' }) {
  if (!error) return null;

  const message = getMessage(error);
  const sessionLost = isSessionLost(error);
  const network = isNetworkError(error);

  let title = 'Something went wrong';
  let body = message;

  if (sessionLost) {
    title = 'Session lost';
    body =
      "We couldn't find your session on the server — it may have expired, or the backend " +
      "restarted. Anything typed so far on this screen isn't recoverable, but starting a new " +
      'session only takes a few seconds.';
  } else if (network) {
    title = "Can't reach the backend";
  }

  return (
    <div
      className={'error-notice' + (sessionLost ? ' error-notice--session' : '')}
      role="alert"
    >
      <p className="error-notice__title">{title}</p>
      <p className="error-notice__message">{body}</p>
      {(onRetry || onRestart) && (
        <div className="error-notice__actions">
          {onRetry && (
            <button type="button" className="error-notice__retry" onClick={onRetry}>
              {retryLabel}
            </button>
          )}
          {onRestart && (
            <button
              type="button"
              className={
                'error-notice__restart' +
                (sessionLost ? ' error-notice__restart--primary' : '')
              }
              onClick={onRestart}
            >
              Start a new session
            </button>
          )}
        </div>
      )}
    </div>
  );
}
