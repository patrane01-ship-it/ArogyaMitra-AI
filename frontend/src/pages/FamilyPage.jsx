import React, { useEffect, useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { useFamily } from '../context/FamilyContext';
import { addFamilyMember, deactivateFamilyMember } from '../services/familyApi';
import { Plus, Trash2, UserCircle, X, Loader2, AlertCircle } from 'lucide-react';

const RELATIONS = ['SELF', 'SPOUSE', 'PARENT', 'CHILD', 'SIBLING', 'OTHER'];
const GENDERS = ['MALE', 'FEMALE', 'OTHER'];
const RELATION_EMOJI = {
  SELF: '👤', SPOUSE: '💑', PARENT: '👴', CHILD: '👶', SIBLING: '👫', OTHER: '🧑',
};

const cardStyle = {
  background: '#fff', borderRadius: '1rem', border: '1px solid #E2E8F0',
  padding: '1.25rem', boxShadow: '0 2px 6px rgba(0,0,0,0.04)',
  transition: 'all 0.2s',
};

const inputStyle = {
  width: '100%', padding: '0.6rem 0.75rem', borderRadius: '0.5rem',
  border: '1px solid #E2E8F0', fontSize: '0.875rem', color: '#1A202C',
  outline: 'none', boxSizing: 'border-box', transition: 'border-color 0.2s',
  background: '#fff',
};

export default function FamilyPage() {
  const { t } = useTranslation();
  const { members, loadMembers, switchProfile, activeProfile } = useFamily();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    member_name: '', relation: 'SPOUSE', date_of_birth: '', gender: '', abha_id: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const resetForm = () => {
    setForm({ member_name: '', relation: 'SPOUSE', date_of_birth: '', gender: '', abha_id: '' });
    setError('');
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await addFamilyMember({
        member_name: form.member_name,
        relation: form.relation,
        date_of_birth: form.date_of_birth || null,
        gender: form.gender || null,
        abha_id: form.abha_id || null,
      });
      setSuccess(t('family.addSuccess'));
      setShowForm(false);
      resetForm();
      await loadMembers();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      const msg = err.response?.data?.message || t('common.error');
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleDeactivate = async (m) => {
    if (!window.confirm(t('family.deactivateConfirm'))) return;
    try {
      await deactivateFamilyMember(m.profile_id);
      await loadMembers();
    } catch (err) {
      alert(err.response?.data?.message || t('common.error'));
    }
  };

  const computeAge = (dob) => {
    if (!dob) return null;
    const d = new Date(dob);
    const today = new Date();
    let age = today.getFullYear() - d.getFullYear();
    if (today.getMonth() < d.getMonth() || (today.getMonth() === d.getMonth() && today.getDate() < d.getDate())) {
      age--;
    }
    return age >= 0 ? age : null;
  };

  return (
    <div style={{ maxWidth: '700px', margin: '0 auto', padding: '2rem 1rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontWeight: 800, color: '#1A202C', fontSize: '1.5rem', margin: 0 }}>
            {t('family.title')}
          </h1>
          <p style={{ color: '#64748B', fontSize: '0.85rem', margin: '0.25rem 0 0' }}>
            {members.length} member{members.length !== 1 ? 's' : ''} · Viewing: <strong>{activeProfile?.member_name || 'Me'}</strong>
          </p>
        </div>
        <button
          onClick={() => { setShowForm(s => !s); resetForm(); }}
          style={{
            display: 'flex', alignItems: 'center', gap: '0.4rem',
            padding: '0.55rem 1.1rem', borderRadius: '0.6rem', border: 'none',
            background: 'linear-gradient(135deg, #4ECBA0, #1a8c68)',
            color: '#fff', fontWeight: 700, fontSize: '0.85rem',
            cursor: 'pointer', boxShadow: '0 4px 12px rgba(78,203,160,0.3)',
          }}
        >
          {showForm ? <X size={15} /> : <Plus size={15} />}
          {showForm ? t('common.cancel') : t('family.addMember')}
        </button>
      </div>

      {/* Success message */}
      {success && (
        <div style={{
          background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '0.6rem',
          padding: '0.6rem 0.85rem', color: '#166534', fontSize: '0.85rem',
          marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.4rem',
        }}>
          ✅ {success}
        </div>
      )}

      {/* Add Member Form */}
      {showForm && (
        <div style={{ ...cardStyle, marginBottom: '1.5rem', border: '1px solid rgba(78,203,160,0.3)' }}>
          <h2 style={{ fontWeight: 700, color: '#1A202C', fontSize: '1rem', margin: '0 0 1rem' }}>
            {t('family.addMember')}
          </h2>
          <form onSubmit={handleAdd}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={{ color: '#64748B', fontSize: '0.8rem', display: 'block', marginBottom: '0.3rem' }}>
                  {t('family.memberName')} *
                </label>
                <input
                  required value={form.member_name}
                  onChange={e => setForm(f => ({ ...f, member_name: e.target.value }))}
                  style={inputStyle} placeholder="Full name"
                />
              </div>
              <div>
                <label style={{ color: '#64748B', fontSize: '0.8rem', display: 'block', marginBottom: '0.3rem' }}>
                  {t('family.relation')} *
                </label>
                <select
                  required value={form.relation}
                  onChange={e => setForm(f => ({ ...f, relation: e.target.value }))}
                  style={inputStyle}
                >
                  {RELATIONS.filter(r => r !== 'SELF').map(r => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </div>
              <div>
                <label style={{ color: '#64748B', fontSize: '0.8rem', display: 'block', marginBottom: '0.3rem' }}>
                  {t('family.gender')}
                </label>
                <select
                  value={form.gender}
                  onChange={e => setForm(f => ({ ...f, gender: e.target.value }))}
                  style={inputStyle}
                >
                  <option value="">Select</option>
                  {GENDERS.map(g => <option key={g} value={g}>{g}</option>)}
                </select>
              </div>
              <div>
                <label style={{ color: '#64748B', fontSize: '0.8rem', display: 'block', marginBottom: '0.3rem' }}>
                  {t('family.dateOfBirth')}
                </label>
                <input
                  type="date" value={form.date_of_birth}
                  onChange={e => setForm(f => ({ ...f, date_of_birth: e.target.value }))}
                  style={inputStyle}
                />
              </div>
              <div>
                <label style={{ color: '#64748B', fontSize: '0.8rem', display: 'block', marginBottom: '0.3rem' }}>
                  {t('family.abhaId')} <span style={{ color: '#CBD5E1', fontSize: '0.7rem' }}>(14-digit)</span>
                </label>
                <input
                  type="text" value={form.abha_id} maxLength={14}
                  onChange={e => setForm(f => ({ ...f, abha_id: e.target.value }))}
                  style={inputStyle} placeholder="Optional"
                />
              </div>
            </div>

            {error && (
              <div style={{
                background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: '0.5rem',
                padding: '0.6rem 0.75rem', color: '#991B1B', fontSize: '0.8rem', marginTop: '0.75rem',
                display: 'flex', alignItems: 'center', gap: '0.4rem',
              }}>
                <AlertCircle size={14} /> {error}
              </div>
            )}

            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
              <button type="submit" disabled={loading} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem',
                padding: '0.6rem 1.25rem', borderRadius: '0.6rem', border: 'none',
                background: loading ? '#E2E8F0' : 'linear-gradient(135deg, #4ECBA0, #1a8c68)',
                color: loading ? '#94A3B8' : '#fff', fontWeight: 700, fontSize: '0.875rem',
                cursor: loading ? 'not-allowed' : 'pointer',
              }}>
                {loading && <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />}
                {t('common.save')}
              </button>
              <button type="button" onClick={() => { setShowForm(false); resetForm(); }} style={{
                padding: '0.6rem 1rem', borderRadius: '0.6rem', border: '1px solid #E2E8F0',
                background: '#fff', color: '#64748B', fontWeight: 600, fontSize: '0.875rem', cursor: 'pointer',
              }}>
                {t('common.cancel')}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Members list */}
      {members.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#CBD5E1' }}>
          <UserCircle size={48} style={{ marginBottom: '0.75rem' }} />
          <p style={{ fontWeight: 600, color: '#94A3B8' }}>{t('family.noMembers')}</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {members.map(m => {
            const isActive = activeProfile?.profile_id === m.profile_id;
            const age = computeAge(m.date_of_birth);
            return (
              <div
                key={m.profile_id}
                style={{
                  ...cardStyle,
                  border: isActive ? '1.5px solid rgba(78,203,160,0.45)' : '1px solid #E2E8F0',
                  boxShadow: isActive ? '0 4px 16px rgba(78,203,160,0.12)' : '0 2px 6px rgba(0,0,0,0.04)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                    <div style={{
                      width: '44px', height: '44px', borderRadius: '50%',
                      background: isActive ? 'rgba(78,203,160,0.15)' : '#F8FAFC',
                      border: isActive ? '2px solid rgba(78,203,160,0.4)' : '2px solid #E2E8F0',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: '1.3rem',
                    }}>
                      {RELATION_EMOJI[m.relation] || '👤'}
                    </div>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ fontWeight: 700, color: '#1A202C', fontSize: '0.95rem' }}>
                          {m.member_name}
                        </span>
                        {m.is_primary && (
                          <span style={{
                            background: 'rgba(78,203,160,0.12)', color: '#1a6b5a',
                            fontSize: '0.68rem', fontWeight: 700, borderRadius: '2rem',
                            padding: '0.1rem 0.5rem',
                          }}>SELF</span>
                        )}
                        {isActive && (
                          <span style={{
                            background: '#4ECBA0', color: '#fff',
                            fontSize: '0.65rem', fontWeight: 700, borderRadius: '2rem',
                            padding: '0.1rem 0.5rem', letterSpacing: '0.03em',
                          }}>ACTIVE</span>
                        )}
                      </div>
                      <div style={{ color: '#94A3B8', fontSize: '0.78rem', marginTop: '0.15rem' }}>
                        {m.relation}
                        {m.gender ? ` · ${m.gender}` : ''}
                        {age !== null ? ` · ${age} yrs` : ''}
                        {m.abha_id ? ` · ABHA: ${m.abha_id}` : ''}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    {!isActive && (
                      <button
                        onClick={() => switchProfile(m)}
                        style={{
                          padding: '0.35rem 0.75rem', borderRadius: '0.5rem',
                          border: '1px solid rgba(78,203,160,0.35)',
                          background: 'rgba(78,203,160,0.08)',
                          color: '#1a6b5a', fontSize: '0.78rem', fontWeight: 600, cursor: 'pointer',
                        }}
                      >
                        {t('family.switchTo')}
                      </button>
                    )}
                    {!m.is_primary && (
                      <button
                        onClick={() => handleDeactivate(m)}
                        style={{
                          padding: '0.35rem', borderRadius: '0.5rem',
                          border: '1px solid #FECACA', background: '#FEF2F2',
                          color: '#ef4444', cursor: 'pointer', display: 'flex', alignItems: 'center',
                        }}
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
