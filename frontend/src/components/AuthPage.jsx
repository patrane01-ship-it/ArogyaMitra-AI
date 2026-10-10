import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { Heart, Eye, EyeOff, Loader2 } from 'lucide-react';

const inputStyle = {
  width: '100%',
  padding: '0.65rem 0.75rem',
  borderRadius: '0.6rem',
  background: 'rgba(255,255,255,0.08)',
  border: '1px solid rgba(255,255,255,0.15)',
  color: '#fff',
  fontSize: '0.9rem',
  outline: 'none',
  boxSizing: 'border-box',
  transition: 'border-color 0.2s',
};

export default function AuthPage({ onAuthenticated }) {
  const { t } = useTranslation();
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [form, setForm] = useState({ email: '', password: '', full_name: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPass, setShowPass] = useState(false);

  const handle = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (isLogin) {
        await login(form.email, form.password);
      } else {
        await register(form.email, form.password, form.full_name);
      }
      onAuthenticated();
    } catch (err) {
      setError(err.response?.data?.message || t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f2027 0%, #203a43 50%, #1a6b5a 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1rem',
      fontFamily: '"Inter", sans-serif',
    }}>
      {/* Decorative blur blobs */}
      <div style={{
        position: 'fixed', top: '-10%', right: '-10%',
        width: '400px', height: '400px', borderRadius: '50%',
        background: 'rgba(78,203,160,0.12)', filter: 'blur(80px)', pointerEvents: 'none',
      }} />
      <div style={{
        position: 'fixed', bottom: '-10%', left: '-10%',
        width: '500px', height: '500px', borderRadius: '50%',
        background: 'rgba(26,107,90,0.15)', filter: 'blur(100px)', pointerEvents: 'none',
      }} />

      <div style={{
        background: 'rgba(255,255,255,0.06)',
        backdropFilter: 'blur(24px)',
        border: '1px solid rgba(255,255,255,0.12)',
        borderRadius: '1.5rem',
        padding: '2.5rem',
        width: '100%',
        maxWidth: '420px',
        boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)',
        position: 'relative',
        zIndex: 1,
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
            color: '#4ECBA0', fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.02em',
          }}>
            <Heart size={28} fill="#4ECBA0" strokeWidth={0} /> ArogyaMitra AI
          </div>
          <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.8rem', marginTop: '0.35rem' }}>
            Personal Health Intelligence System
          </p>
        </div>

        {/* Tab toggle */}
        <div style={{
          display: 'flex',
          background: 'rgba(255,255,255,0.06)',
          borderRadius: '0.75rem',
          padding: '4px',
          marginBottom: '1.75rem',
          gap: '4px',
        }}>
          {[
            { key: true, label: t('auth.login') },
            { key: false, label: t('auth.register') },
          ].map(({ key, label }) => (
            <button key={String(key)} onClick={() => { setIsLogin(key); setError(''); }} style={{
              flex: 1, padding: '0.5rem', borderRadius: '0.55rem', border: 'none',
              background: isLogin === key ? 'rgba(78,203,160,0.2)' : 'transparent',
              color: isLogin === key ? '#4ECBA0' : 'rgba(255,255,255,0.45)',
              fontWeight: 600, cursor: 'pointer', fontSize: '0.875rem',
              transition: 'all 0.2s',
            }}>
              {label}
            </button>
          ))}
        </div>

        <form onSubmit={handle}>
          {!isLogin && (
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ color: 'rgba(255,255,255,0.65)', fontSize: '0.8rem', display: 'block', marginBottom: '0.35rem' }}>
                {t('auth.fullName')}
              </label>
              <input
                type="text" required={!isLogin} autoComplete="name"
                value={form.full_name} onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))}
                style={inputStyle} placeholder="e.g. Arjun Sharma"
              />
            </div>
          )}

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ color: 'rgba(255,255,255,0.65)', fontSize: '0.8rem', display: 'block', marginBottom: '0.35rem' }}>
              {t('auth.email')}
            </label>
            <input
              type="email" required autoComplete="email"
              value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              style={inputStyle} placeholder="you@example.com"
            />
          </div>

          <div style={{ marginBottom: '1.5rem', position: 'relative' }}>
            <label style={{ color: 'rgba(255,255,255,0.65)', fontSize: '0.8rem', display: 'block', marginBottom: '0.35rem' }}>
              {t('auth.password')}
            </label>
            <input
              type={showPass ? 'text' : 'password'} required autoComplete="current-password"
              value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              style={{ ...inputStyle, paddingRight: '2.75rem' }} placeholder="••••••••"
            />
            <button type="button" onClick={() => setShowPass(s => !s)} style={{
              position: 'absolute', right: '0.75rem', top: '2.1rem',
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'rgba(255,255,255,0.35)', padding: 0, display: 'flex',
            }}>
              {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>

          {error && (
            <div style={{
              background: 'rgba(239,68,68,0.12)',
              border: '1px solid rgba(239,68,68,0.25)',
              borderRadius: '0.5rem', padding: '0.65rem',
              color: '#fca5a5', fontSize: '0.82rem', marginBottom: '1rem',
            }}>{error}</div>
          )}

          <button type="submit" disabled={loading} style={{
            width: '100%', padding: '0.75rem', borderRadius: '0.75rem', border: 'none',
            background: loading
              ? 'rgba(78,203,160,0.3)'
              : 'linear-gradient(135deg, #4ECBA0 0%, #1a8c68 100%)',
            color: '#fff', fontWeight: 700, fontSize: '0.95rem',
            cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
            transition: 'all 0.2s',
            boxShadow: loading ? 'none' : '0 4px 20px rgba(78,203,160,0.35)',
          }}>
            {loading && <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />}
            {isLogin ? t('auth.loginBtn') : t('auth.registerBtn')}
          </button>
        </form>

        <p style={{ textAlign: 'center', color: 'rgba(255,255,255,0.35)', fontSize: '0.75rem', marginTop: '1.5rem' }}>
          🔒 AES-256-GCM encrypted · PHI never logged
        </p>
      </div>
    </div>
  );
}
