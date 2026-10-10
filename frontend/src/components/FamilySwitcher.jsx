import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useFamily } from '../context/FamilyContext';
import { ChevronDown, Check, UserCircle } from 'lucide-react';

const RELATION_EMOJI = {
  SELF: '👤', SPOUSE: '💑', PARENT: '👴', CHILD: '👶',
  SIBLING: '👫', OTHER: '🧑',
};

export default function FamilySwitcher() {
  const { t } = useTranslation();
  const { members, activeProfile, switchProfile, loading } = useFamily();
  const [open, setOpen] = useState(false);

  if (loading || !members.length) return null;

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          display: 'flex', alignItems: 'center', gap: '0.4rem',
          padding: '0.35rem 0.7rem', borderRadius: '2rem',
          background: 'rgba(78,203,160,0.15)',
          border: '1px solid rgba(78,203,160,0.35)',
          color: '#1a6b5a', cursor: 'pointer', fontSize: '0.82rem',
          fontWeight: 600, transition: 'all 0.2s', whiteSpace: 'nowrap',
        }}
      >
        <span style={{ fontSize: '1rem' }}>
          {RELATION_EMOJI[activeProfile?.relation] || '👤'}
        </span>
        <span style={{ maxWidth: '100px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {activeProfile?.member_name || t('family.selfProfile')}
        </span>
        <ChevronDown
          size={13}
          style={{ transition: 'transform 0.2s', transform: open ? 'rotate(180deg)' : 'rotate(0deg)' }}
        />
      </button>

      {open && (
        <>
          {/* Backdrop */}
          <div
            style={{ position: 'fixed', inset: 0, zIndex: 998 }}
            onClick={() => setOpen(false)}
          />
          {/* Dropdown */}
          <div style={{
            position: 'absolute', top: 'calc(100% + 0.5rem)', right: 0,
            background: '#fff', border: '1px solid #E2E8F0',
            borderRadius: '0.875rem',
            boxShadow: '0 10px 30px -5px rgba(0,0,0,0.12)',
            minWidth: '200px', zIndex: 999, overflow: 'hidden',
          }}>
            <div style={{ padding: '0.4rem 0.75rem', fontSize: '0.7rem', color: '#94A3B8', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', borderBottom: '1px solid #F1F5F9' }}>
              {t('family.title')}
            </div>
            {members.map((m) => (
              <button
                key={m.profile_id}
                onClick={() => { switchProfile(m); setOpen(false); }}
                style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: '0.65rem',
                  padding: '0.6rem 0.85rem', background: 'none', border: 'none',
                  cursor: 'pointer', textAlign: 'left', transition: 'background 0.12s',
                }}
                onMouseEnter={e => e.currentTarget.style.background = '#F8FAFC'}
                onMouseLeave={e => e.currentTarget.style.background = 'none'}
              >
                <span style={{ fontSize: '1.1rem', lineHeight: 1 }}>
                  {RELATION_EMOJI[m.relation] || '👤'}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, color: '#1A202C', fontSize: '0.85rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {m.member_name}
                  </div>
                  <div style={{ color: '#94A3B8', fontSize: '0.72rem' }}>{m.relation}</div>
                </div>
                {activeProfile?.profile_id === m.profile_id && (
                  <Check size={14} color="#4ECBA0" style={{ flexShrink: 0 }} />
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
