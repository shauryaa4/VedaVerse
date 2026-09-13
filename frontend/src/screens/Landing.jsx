import './Landing.css';

/**
 * FE-01. "Get started" is what actually triggers real session creation
 * (POST /session) in App.jsx's handleStart — nothing here talks to the API
 * directly, this screen is presentation only.
 */
export default function Landing({ onStart, loading, error }) {
  return (
    <div className="landing">
      <div className="landing__card card">
        <p className="landing__eyebrow">AIIA · Ministry of AYUSH · SIH 26045</p>
        <h1 className="landing__title">
          Know how the law treats your Ayurvedic product — before you file anything.
        </h1>
        <p className="landing__body">
          Classical formulation or new combination? India or international? Patent,
          trademark, or regulatory pathway? Answer a few questions and get a
          grounded, citation-backed answer — with a confidence score, and an
          honest "we don't know" when the corpus doesn't cover it.
        </p>

        <ul className="landing__points">
          <li>Formulation-aware classification, not a generic chatbot guess</li>
          <li>Every claim traces back to an actual statute, rule, or treaty section</li>
          <li>India and international answers are kept in separate, labelled lanes</li>
        </ul>

        {error && <p className="landing__error">{error}</p>}

        <button
          type="button"
          className="landing__cta"
          onClick={onStart}
          disabled={loading}
        >
          {loading ? 'Starting session…' : 'Get started'}
        </button>

        <p className="landing__disclaimer">
          This tool provides information, not legal advice.
        </p>
      </div>
    </div>
  );
}
