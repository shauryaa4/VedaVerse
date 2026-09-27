import { useState } from 'react';
import useTranslatedTexts from '../utils/useTranslatedTexts.js';

export default function AccountDialog({ mode, onClose, onSubmit, loading, error, currentLang = 'en' }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [profession, setProfession] = useState('');
  const signingUp = mode === 'signup';
  const uiText = useTranslatedTexts(['Close', 'IP-SAKTI SAHAYAK', 'Create your account', 'Welcome back', 'Your cases are stored in this prototype’s local database and linked to your account.', 'Full name', 'Email', 'Phone number', 'Optional', 'Profession', 'For example, researcher or founder', 'Password', 'Use at least 8 characters. Keep your password private.', 'Please wait…', 'Create account', 'Log in'], currentLang);

  return (
    <div className="account-notice__backdrop" role="presentation" onClick={onClose}>
      <section className="account-notice account-dialog card" role="dialog" aria-modal="true" aria-labelledby="account-notice-title" onClick={(event) => event.stopPropagation()}>
        <button className="account-notice__close" type="button" onClick={onClose} aria-label={uiText('Close')}>×</button>
        <p className="landing__eyebrow">{uiText('IP-SAKTI SAHAYAK')}</p>
        <h2 id="account-notice-title">{signingUp ? uiText('Create your account') : uiText('Welcome back')}</h2>
        <p className="account-dialog__intro">{uiText('Your cases are stored in this prototype’s local database and linked to your account.')}</p>
        <form onSubmit={(event) => { event.preventDefault(); onSubmit({ name, email, password, phone, profession }); }}>
          {signingUp && <label>{uiText('Full name')} <input autoComplete="name" value={name} onChange={(e) => setName(e.target.value)} required maxLength={120} /></label>}
          <label>{uiText('Email')} <input type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
          {signingUp && <label>{uiText('Phone number')} <span>{uiText('Optional')}</span><input type="tel" autoComplete="tel" value={phone} onChange={(e) => setPhone(e.target.value)} maxLength={40} /></label>}
          {signingUp && <label>{uiText('Profession')} <span>{uiText('Optional')}</span><input value={profession} onChange={(e) => setProfession(e.target.value)} maxLength={120} placeholder={uiText('For example, researcher or founder')} /></label>}
          <label>{uiText('Password')} <input type="password" autoComplete={signingUp ? 'new-password' : 'current-password'} value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} maxLength={256} /></label>
          {signingUp && <small className="account-dialog__hint">{uiText('Use at least 8 characters. Keep your password private.')}</small>}
          {error && <p className="account-dialog__error" role="alert">{error.message || error}</p>}
          <button className="landing__cta" type="submit" disabled={loading}>{loading ? uiText('Please wait…') : signingUp ? uiText('Create account') : uiText('Log in')}</button>
        </form>
      </section>
    </div>
  );
}
