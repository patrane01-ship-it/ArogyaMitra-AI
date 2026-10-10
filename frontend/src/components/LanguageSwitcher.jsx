import React from 'react';
import { useTranslation } from 'react-i18next';
import { Languages } from 'lucide-react';

export default function LanguageSwitcher({ dark = false }) {
  const { i18n } = useTranslation();
  const currentLang = i18n.language?.startsWith('hi') ? 'hi' : 'en';

  const toggle = () => {
    const next = currentLang === 'en' ? 'hi' : 'en';
    i18n.changeLanguage(next);
    localStorage.setItem('arogya_lang', next);
  };

  return (
    <button
      onClick={toggle}
      title="Switch Language / भाषा बदलें"
      style={{
        display: 'flex', alignItems: 'center', gap: '0.3rem',
        padding: '0.3rem 0.6rem', borderRadius: '2rem', border: 'none',
        background: dark ? 'rgba(255,255,255,0.1)' : 'rgba(26,107,90,0.08)',
        color: dark ? 'rgba(255,255,255,0.75)' : '#1a6b5a',
        cursor: 'pointer', fontSize: '0.78rem', fontWeight: 700,
        transition: 'all 0.2s',
        letterSpacing: '0.02em',
      }}
    >
      <Languages size={13} />
      {currentLang === 'en' ? 'हिं' : 'EN'}
    </button>
  );
}
