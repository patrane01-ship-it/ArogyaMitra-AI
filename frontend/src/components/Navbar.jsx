import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Heart, Upload, Activity, Bell, FileText, Users, CreditCard, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import LanguageSwitcher from './LanguageSwitcher';
import FamilySwitcher from './FamilySwitcher';

const linkStyle = ({ isActive }) => ({
  display: 'flex', alignItems: 'center', gap: '0.5rem',
  padding: '0.65rem 1rem', borderRadius: '0.75rem',
  textDecoration: 'none',
  background: isActive ? 'rgba(78,203,160,0.1)' : 'transparent',
  color: isActive ? '#4ECBA0' : '#CBD5E1',
  fontWeight: isActive ? 700 : 500,
  transition: 'all 0.2s',
  fontSize: '0.875rem'
});

export default function Navbar() {
  const { t } = useTranslation();
  const { logout } = useAuth();

  return (
    <nav style={{
      width: '240px', background: '#0F172A', minHeight: '100vh',
      padding: '1.5rem 1rem', display: 'flex', flexDirection: 'column',
      borderRight: '1px solid #1E293B',
      position: 'sticky', top: 0
    }}>
      {/* Brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '2rem', padding: '0 0.5rem' }}>
        <Heart size={28} fill="#4ECBA0" strokeWidth={0} />
        <span style={{ color: '#F8FAFC', fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.02em' }}>ArogyaMitra</span>
      </div>

      {/* Profile Switcher */}
      <div style={{ marginBottom: '2rem', padding: '0 0.5rem' }}>
        <FamilySwitcher />
      </div>

      {/* Navigation Links */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', flex: 1 }}>
        <NavLink to="/" style={linkStyle}><Activity size={18} /> {t('nav.dashboard')}</NavLink>
        <NavLink to="/upload" style={linkStyle}><Upload size={18} /> {t('nav.upload')}</NavLink>
        <NavLink to="/timeline" style={linkStyle}><Activity size={18} /> {t('nav.timeline')}</NavLink>
        <NavLink to="/reminders" style={linkStyle}><Bell size={18} /> {t('nav.reminders')}</NavLink>
        <NavLink to="/report" style={linkStyle}><FileText size={18} /> {t('nav.report')}</NavLink>
        <NavLink to="/predictions" style={linkStyle}><Activity size={18} /> {t('nav.predictions')}</NavLink>
        
        <div style={{ margin: '1.5rem 0 0.5rem', borderTop: '1px solid #1E293B', paddingTop: '1.5rem' }} />
        
        <NavLink to="/family" style={linkStyle}><Users size={18} /> {t('nav.family')}</NavLink>
        <NavLink to="/subscription" style={linkStyle}><CreditCard size={18} /> {t('nav.subscription')}</NavLink>
      </div>

      {/* Bottom controls */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '2rem', borderTop: '1px solid #1E293B', paddingTop: '1.5rem' }}>
        <div style={{ padding: '0 0.5rem' }}>
          <LanguageSwitcher dark />
        </div>
        <button
          onClick={logout}
          style={{
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            padding: '0.65rem 1rem', borderRadius: '0.75rem', border: 'none',
            background: 'transparent', color: '#94A3B8', fontWeight: 500,
            cursor: 'pointer', textAlign: 'left', fontSize: '0.875rem',
            transition: 'all 0.2s'
          }}
          onMouseEnter={e => e.currentTarget.style.color = '#ef4444'}
          onMouseLeave={e => e.currentTarget.style.color = '#94A3B8'}
        >
          <LogOut size={18} /> {t('auth.logout')}
        </button>
      </div>
    </nav>
  );
}
