import React, { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Mic, Square, Check, X, Loader2 } from 'lucide-react';
import api from '../services/api';

const btnStyle = (color, outline = false) => ({
  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem',
  padding: '0.55rem', borderRadius: '0.6rem', border: 'none',
  background: outline ? 'transparent' : `${color}18`,
  color: color,
  fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer',
  transition: 'all 0.15s', flex: 1,
});

export default function VoiceInput({ profileId, onSaved }) {
  const { t } = useTranslation();
  const [state, setState] = useState('idle'); // idle | recording | processing | review | saving
  const [transcript, setTranscript] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [error, setError] = useState('');
  const mediaRef = useRef(null);
  const chunksRef = useRef([]);

  const startRecording = async () => {
    setError('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRef.current = mr;
      chunksRef.current = [];
      mr.ondataavailable = e => chunksRef.current.push(e.data);
      mr.onstop = handleStop;
      mr.start();
      setState('recording');
    } catch {
      setError('Microphone access denied. Please allow microphone permissions.');
    }
  };

  const stopRecording = () => {
    mediaRef.current?.stop();
    setState('processing');
  };

  const handleStop = async () => {
    const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append('file', blob, 'voice.webm');
    if (profileId) formData.append('profile_id', profileId);
    try {
      const res = await api.post('/api/voice/transcribe', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setTranscript(res.data.transcript || '');
      setSessionId(res.data.session_id);
      setState('review');
    } catch (e) {
      setError(e.response?.data?.message || t('common.error'));
      setState('idle');
    }
  };

  const confirm = async () => {
    setState('saving');
    try {
      await api.post('/api/voice/confirm', { session_id: sessionId });
      onSaved?.();
      setState('idle');
      setTranscript('');
      setSessionId(null);
    } catch (e) {
      setError(e.response?.data?.message || t('common.error'));
      setState('review');
    }
  };

  const discard = async () => {
    if (sessionId) {
      await api.post('/api/voice/discard', { session_id: sessionId }).catch(() => {});
    }
    setState('idle');
    setTranscript('');
    setSessionId(null);
    setError('');
  };

  return (
    <div style={{
      background: '#fff', borderRadius: '1rem', padding: '1.25rem',
      border: '1px solid #E2E8F0', maxWidth: '380px',
    }}>
      <h3 style={{ fontWeight: 700, color: '#1A202C', fontSize: '0.9rem', margin: '0 0 1rem' }}>
        🎙️ {t('voice.title')}
      </h3>

      {error && (
        <div style={{
          background: '#FEF2F2', border: '1px solid #FECACA',
          borderRadius: '0.5rem', padding: '0.6rem 0.75rem',
          color: '#991B1B', fontSize: '0.8rem', marginBottom: '0.75rem',
        }}>{error}</div>
      )}

      {state === 'idle' && (
        <button onClick={startRecording} style={{
          ...btnStyle('#4ECBA0'),
          width: '100%', padding: '0.7rem',
          background: 'linear-gradient(135deg, #4ECBA0, #1a8c68)',
          color: '#fff',
          boxShadow: '0 4px 12px rgba(78,203,160,0.3)',
        }}>
          <Mic size={16} /> {t('voice.record')}
        </button>
      )}

      {state === 'recording' && (
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '72px', height: '72px', borderRadius: '50%',
            background: 'rgba(239,68,68,0.08)',
            border: '2px solid rgba(239,68,68,0.4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 0.75rem',
            animation: 'pulse 1.5s ease-in-out infinite',
          }}>
            <Mic size={28} color="#ef4444" />
          </div>
          <p style={{ color: '#ef4444', fontWeight: 600, fontSize: '0.85rem', marginBottom: '0.75rem' }}>
            {t('voice.recording')}
          </p>
          <button onClick={stopRecording} style={{
            ...btnStyle('#ef4444'),
            width: '100%', padding: '0.6rem',
          }}>
            <Square size={14} /> {t('voice.stop')}
          </button>
        </div>
      )}

      {state === 'processing' && (
        <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
          <Loader2 size={28} color="#4ECBA0" style={{ animation: 'spin 1s linear infinite' }} />
          <p style={{ color: '#64748B', marginTop: '0.65rem', fontSize: '0.85rem' }}>
            {t('voice.processing')}
          </p>
        </div>
      )}

      {state === 'review' && (
        <div>
          <p style={{ color: '#64748B', fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.4rem' }}>
            {t('voice.transcript')}
          </p>
          <div style={{
            background: '#F8FAFC', borderRadius: '0.6rem', padding: '0.75rem',
            color: '#1A202C', fontSize: '0.9rem', lineHeight: 1.55,
            marginBottom: '0.85rem', border: '1px solid #E2E8F0',
            minHeight: '60px',
          }}>
            {transcript || <span style={{ color: '#CBD5E1' }}>{t('voice.emptyTranscript')}</span>}
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button onClick={confirm} style={{ ...btnStyle('#4ECBA0'), background: 'rgba(78,203,160,0.15)' }}>
              <Check size={14} /> {t('voice.confirm')}
            </button>
            <button onClick={discard} style={{ ...btnStyle('#94A3B8'), background: '#F1F5F9', color: '#64748B' }}>
              <X size={14} /> {t('voice.discard')}
            </button>
          </div>
        </div>
      )}

      {state === 'saving' && (
        <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
          <Loader2 size={28} color="#4ECBA0" style={{ animation: 'spin 1s linear infinite' }} />
        </div>
      )}
    </div>
  );
}
