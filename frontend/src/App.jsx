import EscalationCTA from './components/EscalationCTA.jsx';

/**
 * TEMPORARY. This just proves FE-09 renders correctly in isolation.
 * FE-06 (query screen) and FE-07 (answer screen) will replace this with the
 * real page structure — EscalationCTA should then be mounted once, low in
 * the actual answer screen layout, not duplicated per-screen.
 */
export default function App() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ flex: 1, padding: '32px 24px', fontFamily: 'var(--font-sans)' }}>
        <p style={{ color: '#7a7a7a', fontSize: 14 }}>
          Placeholder content area — FE-06/FE-07 build the real query and answer screens here.
        </p>
      </div>
      <EscalationCTA />
    </div>
  );
}
