import './ConfidenceTrend.css';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';

/**
 * Right-hand column from the wireframe: a line of confidence across the
 * questions asked in this case, with the latest answer's percentage
 * highlighted underneath.
 *
 * Reads only what the frontend already holds: each history turn's
 * result.confidence_score / .confidence / .abstained (POST /query). No extra
 * API call. A withheld (abstained) answer breaks the line and is drawn as an
 * x on the baseline, so a dip is visibly "no answer", not a low number.
 */

const W = 300;
const H = 170;
const PAD = { l: 38, r: 16, t: 14, b: 28 };
const PLOT_W = W - PAD.l - PAD.r;
const PLOT_H = H - PAD.t - PAD.b;
const MAX_POINTS = 10; // keep the x axis readable in a long session

const LEVEL_LABELS = {
  high: 'High confidence',
  medium: 'Medium confidence',
  low: 'Low confidence',
};

const xFor = (index, count) =>
  count === 1 ? PAD.l + PLOT_W / 2 : PAD.l + (index / (count - 1)) * PLOT_W;
const yFor = (score) => PAD.t + (1 - score) * PLOT_H;

export default function ConfidenceTrend({ history = [], currentLang = 'en' }) {
  const uiText = useTranslatedTexts(
    [
      'Confidence across your questions',
      'Ask a question to see confidence here.',
      'No answer',
      'Answer withheld',
      'Question',
      'High confidence',
      'Medium confidence',
      'Low confidence',
    ],
    currentLang
  );

  const all = (Array.isArray(history) ? history : []).filter((t) => t && t.result);
  const offset = Math.max(0, all.length - MAX_POINTS);
  const points = all.slice(offset).map((turn, i) => {
    const abstained = Boolean(turn.result.abstained);
    const score = typeof turn.result.confidence_score === 'number' ? turn.result.confidence_score : null;
    return {
      n: offset + i + 1, // question number within the whole case
      question: turn.question,
      abstained,
      score,
      level: turn.result.confidence,
      plottable: !abstained && score !== null,
    };
  });

  const latest = points[points.length - 1];
  const latestLevel = latest && !latest.abstained ? latest.level || 'low' : 'none';
  const latestPct = latest && latest.plottable ? Math.round(latest.score * 100) : null;

  // Break the line wherever an answer was withheld.
  const segments = [];
  let current = [];
  points.forEach((p, i) => {
    if (p.plottable) current.push({ ...p, i });
    else if (current.length) { segments.push(current); current = []; }
  });
  if (current.length) segments.push(current);

  return (
    <section className={`confidence-trend confidence-trend--${latestLevel}`}>
      <p className="confidence-trend__title">{uiText('Confidence across your questions')}</p>

      {points.length === 0 ? (
        <p className="confidence-trend__empty">{uiText('Ask a question to see confidence here.')}</p>
      ) : (
        <>
          <svg
            className="confidence-trend__chart"
            viewBox={`0 0 ${W} ${H}`}
            role="img"
            aria-label={`Confidence for ${points.length} question${points.length === 1 ? '' : 's'}`}
          >
            {[0, 0.5, 1].map((tick) => (
              <g key={tick}>
                <line className="confidence-trend__grid" x1={PAD.l} x2={W - PAD.r} y1={yFor(tick)} y2={yFor(tick)} />
                <text className="confidence-trend__tick" x={PAD.l - 6} y={yFor(tick) + 3} textAnchor="end">
                  {Math.round(tick * 100)}
                </text>
              </g>
            ))}

            {segments.map((segment, s) =>
              segment.length > 1 ? (
                <polyline
                  key={s}
                  className="confidence-trend__line"
                  points={segment.map((p) => `${xFor(p.i, points.length)},${yFor(p.score)}`).join(' ')}
                />
              ) : null
            )}

            {points.map((p, i) => {
              const x = xFor(i, points.length);
              const isLatest = i === points.length - 1;
              const tip = `${uiText('Question')} ${p.n}: ${p.question}\n${
                p.plottable ? `${Math.round(p.score * 100)}%` : uiText('Answer withheld')
              }`;
              return (
                <g key={i}>
                  {p.plottable ? (
                    <circle
                      className={`confidence-trend__dot${isLatest ? ' confidence-trend__dot--latest' : ''}`}
                      cx={x}
                      cy={yFor(p.score)}
                      r={isLatest ? 5.5 : 4}
                    >
                      <title>{tip}</title>
                    </circle>
                  ) : p.abstained ? (
                    <g className="confidence-trend__miss" transform={`translate(${x} ${yFor(0)})`}>
                      <line x1="-4" y1="-4" x2="4" y2="4" />
                      <line x1="-4" y1="4" x2="4" y2="-4" />
                      <title>{tip}</title>
                    </g>
                  ) : null}
                  <text className="confidence-trend__xlabel" x={x} y={H - 8} textAnchor="middle">
                    {p.n}
                  </text>
                </g>
              );
            })}
          </svg>

          <div className="confidence-trend__latest">
            <span className="confidence-trend__pct">{latestPct !== null ? `${latestPct}%` : '—'}</span>
            <span className="confidence-trend__label">
              {latest.abstained
                ? uiText('No answer')
                : uiText(LEVEL_LABELS[latestLevel] || latestLevel)}
            </span>
          </div>
        </>
      )}
    </section>
  );
}
