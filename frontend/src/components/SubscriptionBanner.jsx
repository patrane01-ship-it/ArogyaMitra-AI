import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Zap, ArrowUpRight, Crown, Check } from 'lucide-react';
import { getSubscription } from '../services/subscriptionApi';
import { useAuth } from '../context/AuthContext';

const TIER_CONFIG = {
  FREE:    { label: 'Free',    icon: '🆓', color: '#64748B', bg: 'linear-gradient(135deg, #F8FAFC, #F1F5F9)', border: '#E2E8F0' },
  PREMIUM: { label: 'Premium', icon: '⭐', color: '#d97706', bg: 'linear-gradient(135deg, #FFFBEB, #FEF3C7)', border: '#FDE68A' },
  PRO:     { label: 'Pro',     icon: '👑', color: '#7c3aed', bg: 'linear-gradient(135deg, #F5F3FF, #EDE9FE)', border: '#DDD6FE' },
};

export default function SubscriptionBanner({ onUpgradeClick }) {
  const { t } = useTranslation();
  const { token } = useAuth();
  const [sub, setSub] = useState(null);

  useEffect(() => {
    if (!token) return;
    getSubscription()
      .then(d => setSub(d.subscription))
      .catch(() => {});
  }, [token]);

  if (!sub) return null;

  const cfg = TIER_CONFIG[sub.tier] || TIER_CONFIG.FREE;

  return (
    <div style={{
      background: cfg.bg,
      border: `1px solid ${cfg.border}`,
      borderRadius: '1rem',
      padding: '1rem 1.25rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '1rem',
      flexWrap: 'wrap',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <span style={{ fontSize: '1.75rem', lineHeight: 1 }}>{cfg.icon}</span>
        <div>
          <div style={{ fontWeight: 700, color: '#1A202C', fontSize: '0.9rem' }}>
            {cfg.label} {t('subscription.currentPlan')}
          </div>
          <div style={{ color: '#64748B', fontSize: '0.75rem', marginTop: '0.1rem' }}>
            {sub.expires_at
              ? `${t('subscription.expiresOn')}: ${new Date(sub.expires_at).toLocaleDateString()}`
              : t('subscription.neverExpires')}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flexWrap: 'wrap' }}>
        {sub.prediction_enabled && <FeatureChip label="Predictions" />}
        {sub.wearable_enabled && <FeatureChip label="Wearables" />}
        {sub.api_access_enabled && <FeatureChip label="API" />}

        {sub.tier === 'FREE' && onUpgradeClick && (
          <button
            onClick={onUpgradeClick}
            style={{
              display: 'flex', alignItems: 'center', gap: '0.35rem',
              padding: '0.45rem 1rem', borderRadius: '2rem', border: 'none',
              background: 'linear-gradient(135deg, #f59e0b, #d97706)',
              color: '#fff', fontWeight: 700, fontSize: '0.8rem',
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(245,158,11,0.35)',
              transition: 'all 0.2s',
            }}
          >
            <Zap size={13} /> {t('subscription.upgrade')} <ArrowUpRight size={13} />
          </button>
        )}
      </div>
    </div>
  );
}

function FeatureChip({ label }) {
  return (
    <span style={{
      background: 'rgba(78,203,160,0.12)',
      color: '#1a6b5a',
      borderRadius: '2rem',
      padding: '0.2rem 0.6rem',
      fontSize: '0.72rem',
      fontWeight: 600,
      display: 'flex', alignItems: 'center', gap: '0.2rem',
    }}>
      <Check size={11} /> {label}
    </span>
  );
}
