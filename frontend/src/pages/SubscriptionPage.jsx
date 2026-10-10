import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { getSubscription } from '../services/subscriptionApi';
import SubscriptionBanner from '../components/SubscriptionBanner';
import { Check, X, AlertCircle } from 'lucide-react';

const PLANS = [
  {
    tier: 'FREE',
    price: '₹0',
    features: [
      { name: 'Family Members', value: '2' },
      { name: 'Doctor Access Slots', value: '0' },
      { name: 'Health Predictions', included: false },
      { name: 'Wearable Sync', included: false },
      { name: 'API Access', included: false },
    ],
  },
  {
    tier: 'PREMIUM',
    price: '₹999/yr',
    features: [
      { name: 'Family Members', value: '5' },
      { name: 'Doctor Access Slots', value: '3' },
      { name: 'Health Predictions', included: true },
      { name: 'Wearable Sync', included: true },
      { name: 'API Access', included: false },
    ],
  },
  {
    tier: 'PRO',
    price: '₹2499/yr',
    features: [
      { name: 'Family Members', value: '10' },
      { name: 'Doctor Access Slots', value: 'Unlimited' },
      { name: 'Health Predictions', included: true },
      { name: 'Wearable Sync', included: true },
      { name: 'API Access', included: true },
    ],
  },
];

export default function SubscriptionPage() {
  const { t } = useTranslation();
  const [currentTier, setCurrentTier] = useState('FREE');

  useEffect(() => {
    getSubscription().then(d => {
      if (d.subscription) setCurrentTier(d.subscription.tier);
    }).catch(() => {});
  }, []);

  const handleUpgrade = () => {
    alert('Razorpay integration — coming soon');
  };

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', padding: '2rem 1rem' }}>
      <h1 style={{ fontWeight: 800, color: '#1A202C', fontSize: '1.75rem', margin: '0 0 1.5rem' }}>
        {t('subscription.title')}
      </h1>

      <div style={{ marginBottom: '2.5rem' }}>
        <SubscriptionBanner onUpgradeClick={handleUpgrade} />
      </div>

      <h2 style={{ fontWeight: 700, color: '#1A202C', fontSize: '1.25rem', margin: '0 0 1.5rem' }}>
        Choose your plan
      </h2>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
        {PLANS.map(plan => {
          const isCurrent = plan.tier === currentTier;
          return (
            <div key={plan.tier} style={{
              background: '#fff',
              borderRadius: '1.25rem',
              border: isCurrent ? '2px solid #4ECBA0' : '1px solid #E2E8F0',
              padding: '1.5rem',
              boxShadow: isCurrent ? '0 10px 25px -5px rgba(78,203,160,0.2)' : '0 4px 6px -1px rgba(0,0,0,0.05)',
              position: 'relative',
              display: 'flex', flexDirection: 'column'
            }}>
              {isCurrent && (
                <div style={{
                  position: 'absolute', top: '-12px', left: '50%', transform: 'translateX(-50%)',
                  background: '#4ECBA0', color: '#fff', padding: '0.2rem 0.75rem', borderRadius: '1rem',
                  fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.05em'
                }}>
                  CURRENT PLAN
                </div>
              )}
              
              <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
                <h3 style={{ fontWeight: 800, color: '#1A202C', fontSize: '1.25rem', margin: '0 0 0.5rem' }}>
                  {plan.tier}
                </h3>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#1a6b5a' }}>
                  {plan.price}
                </div>
              </div>

              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.85rem', marginBottom: '2rem' }}>
                {plan.features.map((f, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.875rem' }}>
                    {f.value !== undefined ? (
                      <Check size={16} color="#4ECBA0" style={{ flexShrink: 0 }} />
                    ) : f.included ? (
                      <Check size={16} color="#4ECBA0" style={{ flexShrink: 0 }} />
                    ) : (
                      <X size={16} color="#CBD5E1" style={{ flexShrink: 0 }} />
                    )}
                    <span style={{ color: f.included === false && f.value === undefined ? '#94A3B8' : '#475569' }}>
                      {f.name} {f.value ? <strong>{f.value}</strong> : ''}
                    </span>
                  </div>
                ))}
              </div>

              {!isCurrent && (
                <button
                  onClick={handleUpgrade}
                  style={{
                    width: '100%', padding: '0.75rem', borderRadius: '0.75rem', border: 'none',
                    background: plan.tier === 'PRO' ? 'linear-gradient(135deg, #8b5cf6, #6d28d9)' : 'linear-gradient(135deg, #f59e0b, #d97706)',
                    color: '#fff', fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer',
                    boxShadow: plan.tier === 'PRO' ? '0 4px 14px rgba(139,92,246,0.3)' : '0 4px 14px rgba(245,158,11,0.3)',
                  }}
                >
                  Upgrade to {plan.tier}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
