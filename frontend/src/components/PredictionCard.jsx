import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { TrendingUp, TrendingDown, Minus, AlertTriangle, Play, Loader2 } from 'lucide-react';
import { runPrediction } from '../services/predictionApi';
import { useFamily } from '../context/FamilyContext';

const TREND_CONFIG = {
  STABLE:    { color: '#4ECBA0', Icon: Minus,        label: 'Stable'    },
  IMPROVING: { color: '#22d3ee', Icon: TrendingDown,  label: 'Improving' },
  WORSENING: { color: '#f59e0b', Icon: TrendingUp,    label: 'Worsening' },
  VOLATILE:  { color: '#94a3b8', Icon: AlertTriangle, label: 'Volatile'  },
};

const ALERT_STYLE = {
  NONE:   { bg: '#f0fdf4', color: '#166534', border: '#bbf7d0', label: 'Normal'  },
  WATCH:  { bg: '#fefce8', color: '#854d0e', border: '#fef08a', label: 'Watch'   },
  WARN:   { bg: '#fff7ed', color: '#c2410c', border: '#fed7aa', label: 'Warning' },
  URGENT: { bg: '#fef2f2', color: '#991b1b', border: '#fecaca', label: 'Urgent'  },
};

function Stat({ label, value }) {
  return (
    <div style={{ flex: '1 1 80px', minWidth: 72 }}>
      <div style={{ color: '#94A3B8', fontSize: '0.68rem', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>
        {label}
      </div>
      <div style={{ fontWeight: 700, color: '#1A202C', fontSize: '0.95rem', marginTop: '0.1rem' }}>
        {value}
      </div>
    </div>
  );
}

export default function PredictionCard({ paramName }) {
  const { t } = useTranslation();
  const { activeProfile } = useFamily();
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const run = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await runPrediction(paramName, activeProfile?.profile_id);
      setPrediction(data.prediction);
    } catch (e) {
      const msg = e.response?.data?.message || t('common.error');
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const tCfg = prediction ? (TREND_CONFIG[prediction.current_trend] || TREND_CONFIG.STABLE) : null;
  const aCfg = prediction ? (ALERT_STYLE[prediction.alert_level] || ALERT_STYLE.NONE) : null;
  const TrendIcon = tCfg?.Icon;

  return (
    <div style={{
      background: '#fff', borderRadius: '1rem', padding: '1.25rem',
      border: '1px solid #E2E8F0',
      boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
      transition: 'box-shadow 0.2s, transform 0.2s',
    }}
      onMouseEnter={e => { e.currentTarget.style.boxShadow = '0 8px 24px rgba(26,107,90,0.1)'; e.currentTarget.style.transform = 'translateY(-1px)'; }}
      onMouseLeave={e => { e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.04)'; e.currentTarget.style.transform = 'translateY(0)'; }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
        <div>
          <h3 style={{ fontWeight: 700, color: '#1A202C', fontSize: '0.95rem', margin: 0 }}>{paramName}</h3>
          <p style={{ color: '#94A3B8', fontSize: '0.75rem', margin: '0.15rem 0 0' }}>{t('prediction.title')}</p>
        </div>
        <button
          onClick={run}
          disabled={loading}
          style={{
            display: 'flex', alignItems: 'center', gap: '0.3rem',
            padding: '0.35rem 0.8rem', borderRadius: '2rem', border: 'none',
            background: loading
              ? '#F1F5F9'
              : 'linear-gradient(135deg, #4ECBA0, #1a8c68)',
            color: loading ? '#94A3B8' : '#fff',
            fontWeight: 600, fontSize: '0.78rem',
            cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s',
            boxShadow: loading ? 'none' : '0 2px 8px rgba(78,203,160,0.3)',
          }}
        >
          {loading
            ? <Loader2 size={13} style={{ animation: 'spin 1s linear infinite' }} />
            : <Play size={13} />}
          {t('prediction.runPrediction')}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div style={{
          background: '#FEF2F2', border: '1px solid #FECACA',
          borderRadius: '0.5rem', padding: '0.6rem 0.75rem',
          color: '#991B1B', fontSize: '0.8rem', marginBottom: '0.75rem',
        }}>{error}</div>
      )}

      {/* Prediction result */}
      {prediction && (
        <>
          {/* Alert badge */}
          {prediction.alert_level !== 'NONE' && (
            <div style={{
              background: aCfg.bg, border: `1px solid ${aCfg.border}`,
              borderRadius: '0.5rem', padding: '0.55rem 0.75rem',
              color: aCfg.color, fontSize: '0.8rem', fontWeight: 600,
              marginBottom: '0.75rem',
            }}>
              ⚠️ {aCfg.label}
            </div>
          )}

          {/* Narrative */}
          <p style={{
            color: '#475569', fontSize: '0.85rem', lineHeight: 1.6,
            background: '#F8FAFC', borderRadius: '0.5rem', padding: '0.65rem 0.75rem',
            marginBottom: '0.75rem', fontStyle: 'italic',
          }}>
            {prediction.narrative}
          </p>

          {/* Stats row */}
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            <Stat label={t('prediction.currentValue')} value={prediction.current_value?.toFixed(1)} />
            <Stat label={t('prediction.confidence')} value={`${(prediction.confidence * 100).toFixed(0)}%`} />
            <Stat
              label={t('prediction.trend')}
              value={
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.2rem', color: tCfg.color }}>
                  {TrendIcon && <TrendIcon size={14} />}
                  {tCfg.label}
                </span>
              }
            />
            {prediction.months_to_threshold && (
              <Stat
                label={t('prediction.monthsToThreshold')}
                value={`${Math.min(prediction.months_to_threshold, 36)}${prediction.months_to_threshold >= 36 ? '+' : ''} mo`}
              />
            )}
          </div>
        </>
      )}

      {/* Empty state */}
      {!prediction && !loading && !error && (
        <p style={{ color: '#CBD5E1', fontSize: '0.82rem', textAlign: 'center', padding: '0.75rem 0' }}>
          {t('prediction.noPredictions')}
        </p>
      )}
    </div>
  );
}
