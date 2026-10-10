import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import api from '../services/api';
import { Heart, Activity, AlertTriangle, FileText, Loader2, XCircle } from 'lucide-react';
import RiskGauge from '../components/RiskGauge';

export default function DoctorWorkspacePage({ token }) {
  const { t } = useTranslation();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchWorkspace = async () => {
      try {
        const res = await api.get(`/doctor-view/${token}`);
        setData(res.data);
      } catch (err) {
        if (err.response?.status === 410) {
          setError('This workspace link has expired or been revoked by the patient.');
        } else {
          setError(err.response?.data?.message || 'Failed to load workspace.');
        }
      } finally {
        setLoading(false);
      }
    };
    fetchWorkspace();
  }, [token]);

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#F7FAF9' }}>
        <Loader2 size={32} color="#4ECBA0" style={{ animation: 'spin 1s linear infinite' }} />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#F7FAF9', padding: '1rem' }}>
        <div style={{ background: '#fff', padding: '2rem', borderRadius: '1rem', border: '1px solid #E2E8F0', maxWidth: '400px', textAlign: 'center' }}>
          <XCircle size={48} color="#ef4444" style={{ margin: '0 auto 1rem' }} />
          <h2 style={{ color: '#1A202C', fontWeight: 700, margin: '0 0 0.5rem' }}>Access Denied</h2>
          <p style={{ color: '#64748B', fontSize: '0.9rem', margin: 0 }}>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: '#F7FAF9', fontFamily: '"Inter", sans-serif' }}>
      {/* Header */}
      <header style={{
        background: '#fff', borderBottom: '1px solid #E2E8F0',
        padding: '1rem 1.5rem', position: 'sticky', top: 0, zIndex: 10,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#1a6b5a', fontWeight: 700, fontSize: '1.25rem' }}>
          <Heart size={24} fill="#4ECBA0" strokeWidth={0} />
          ArogyaMitra <span style={{ color: '#94A3B8', fontWeight: 400 }}>| Doctor Workspace</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontWeight: 600, color: '#1A202C', fontSize: '0.85rem' }}>Dr. {data.access.doctor_name}</div>
            <div style={{ color: '#64748B', fontSize: '0.75rem' }}>Read-only Access</div>
          </div>
        </div>
      </header>

      <main style={{ maxWidth: '900px', margin: '0 auto', padding: '2rem 1rem' }}>
        {/* Patient Profile */}
        <section style={{ marginBottom: '2rem' }}>
          <div style={{ background: '#fff', borderRadius: '1rem', border: '1px solid #E2E8F0', padding: '1.5rem', display: 'flex', gap: '1.5rem', alignItems: 'center', boxShadow: '0 2px 4px rgba(0,0,0,0.02)' }}>
            <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(78,203,160,0.1)', border: '2px solid rgba(78,203,160,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '2rem' }}>
              👤
            </div>
            <div>
              <h1 style={{ fontWeight: 800, color: '#1A202C', fontSize: '1.5rem', margin: '0 0 0.25rem' }}>
                {data.patient.name}
              </h1>
              <p style={{ color: '#64748B', fontSize: '0.9rem', margin: 0 }}>
                {data.patient.age ? `${data.patient.age} yrs` : 'Age unknown'}
                {data.patient.gender ? ` • ${data.patient.gender}` : ''}
              </p>
            </div>
          </div>
        </section>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
          
          {/* Risk Profile */}
          {data.scope.includes('risk') && data.risk_profile && (
            <section style={{ background: '#fff', borderRadius: '1rem', border: '1px solid #E2E8F0', padding: '1.5rem' }}>
              <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, fontSize: '1.1rem', margin: '0 0 1.5rem', color: '#1A202C' }}>
                <AlertTriangle size={18} color="#f59e0b" /> Risk Assessment
              </h2>
              <RiskGauge score={data.risk_profile.score} />
              <div style={{ marginTop: '1rem', background: '#F8FAFC', borderRadius: '0.5rem', padding: '0.75rem', fontSize: '0.85rem', color: '#475569' }}>
                {data.risk_profile.factors.map((f, i) => <div key={i}>• {f}</div>)}
              </div>
            </section>
          )}

          {/* Clinical Parameters */}
          {data.scope.includes('timeline') && data.parameters && (
            <section style={{ background: '#fff', borderRadius: '1rem', border: '1px solid #E2E8F0', padding: '1.5rem' }}>
              <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, fontSize: '1.1rem', margin: '0 0 1.5rem', color: '#1A202C' }}>
                <Activity size={18} color="#4ECBA0" /> Clinical Parameters
              </h2>
              {Object.keys(data.parameters).length === 0 ? (
                <p style={{ color: '#94A3B8', fontSize: '0.85rem' }}>No clinical data available.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {Object.entries(data.parameters).map(([name, val]) => (
                    <div key={name} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid #F1F5F9' }}>
                      <span style={{ color: '#64748B', fontSize: '0.85rem', fontWeight: 500 }}>{name}</span>
                      <span style={{ color: '#1A202C', fontSize: '0.9rem', fontWeight: 700 }}>{val}</span>
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}
        </div>

        {/* Health Records */}
        {data.scope.includes('records') && data.records && (
          <section style={{ background: '#fff', borderRadius: '1rem', border: '1px solid #E2E8F0', padding: '1.5rem', marginTop: '1.5rem' }}>
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, fontSize: '1.1rem', margin: '0 0 1.5rem', color: '#1A202C' }}>
              <FileText size={18} color="#3b82f6" /> Recent Records
            </h2>
            {data.records.length === 0 ? (
              <p style={{ color: '#94A3B8', fontSize: '0.85rem' }}>No recent records available.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {data.records.map(r => (
                  <div key={r.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem', background: '#F8FAFC', borderRadius: '0.5rem', border: '1px solid #E2E8F0' }}>
                    <div>
                      <div style={{ fontWeight: 600, color: '#1A202C', fontSize: '0.85rem' }}>{r.type}</div>
                      <div style={{ color: '#64748B', fontSize: '0.75rem' }}>{r.date}</div>
                    </div>
                    {r.url && (
                      <a href={r.url} target="_blank" rel="noreferrer" style={{ color: '#4ECBA0', fontSize: '0.8rem', fontWeight: 600, textDecoration: 'none' }}>
                        View
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

      </main>
    </div>
  );
}
