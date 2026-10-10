import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { listPredictions } from '../services/predictionApi';
import PredictionCard from '../components/PredictionCard';
import { useFamily } from '../context/FamilyContext';
import { Activity, Lock } from 'lucide-react';
import { getSubscription } from '../services/subscriptionApi';

export default function PredictionsPage() {
  const { t } = useTranslation();
  const { activeProfile } = useFamily();
  const [params, setParams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [premiumGated, setPremiumGated] = useState(false);

  useEffect(() => {
    const checkAccessAndLoad = async () => {
      setLoading(true);
      try {
        const subRes = await getSubscription();
        if (!subRes.subscription?.prediction_enabled) {
          setPremiumGated(true);
          setLoading(false);
          return;
        }
        
        // Load predictions
        const res = await listPredictions(activeProfile?.profile_id);
        // Extract unique param names from existing predictions, or provide defaults if none exist
        const pNames = res.predictions?.map(p => p.param_name) || [];
        const unique = [...new Set([...pNames, 'Glucose (Fasting)', 'HbA1c', 'Cholesterol'])];
        setParams(unique);
      } catch (err) {
        if (err.response?.status === 403) setPremiumGated(true);
      } finally {
        setLoading(false);
      }
    };
    if (activeProfile) checkAccessAndLoad();
  }, [activeProfile]);

  if (premiumGated) {
    return (
      <div style={{ maxWidth: '800px', margin: '0 auto', padding: '3rem 1rem', textAlign: 'center' }}>
        <div style={{ background: '#fff', borderRadius: '1rem', padding: '3rem 2rem', border: '1px solid #E2E8F0', boxShadow: '0 10px 25px -5px rgba(0,0,0,0.05)' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: '#FEF3C7', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem' }}>
            <Lock size={32} color="#f59e0b" />
          </div>
          <h2 style={{ fontWeight: 800, color: '#1A202C', fontSize: '1.5rem', margin: '0 0 1rem' }}>
            Premium Feature
          </h2>
          <p style={{ color: '#64748B', fontSize: '1rem', maxWidth: '400px', margin: '0 auto 2rem', lineHeight: 1.6 }}>
            {t('prediction.premiumRequired')} Upgrade your subscription to unlock AI-powered health trajectory forecasting.
          </p>
          <a href="/subscription" style={{
            display: 'inline-block', padding: '0.75rem 2rem', borderRadius: '2rem',
            background: 'linear-gradient(135deg, #f59e0b, #d97706)', color: '#fff',
            fontWeight: 700, textDecoration: 'none', boxShadow: '0 4px 14px rgba(245,158,11,0.3)'
          }}>
            View Plans
          </a>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '2rem 1rem' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontWeight: 800, color: '#1A202C', fontSize: '1.75rem', margin: '0 0 0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Activity size={28} color="#4ECBA0" /> {t('prediction.title')}
        </h1>
        <p style={{ color: '#64748B', fontSize: '0.9rem', margin: 0 }}>
          AI-driven forecasting for your clinical parameters based on historical trends.
        </p>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem' }}>Loading predictions...</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.5rem' }}>
          {params.map(p => (
            <PredictionCard key={p} paramName={p} />
          ))}
        </div>
      )}
    </div>
  );
}
