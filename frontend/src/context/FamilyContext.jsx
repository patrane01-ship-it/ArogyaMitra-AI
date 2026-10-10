import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { listFamilyMembers } from '../services/familyApi';

const FamilyContext = createContext(null);

export function FamilyProvider({ children }) {
  const { token } = useAuth();
  const [members, setMembers] = useState([]);
  const [activeProfile, setActiveProfile] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadMembers = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await listFamilyMembers();
      const list = data.members || [];
      setMembers(list);
      // Default to SELF (is_primary) if no active profile set
      const self = list.find(m => m.is_primary);
      if (self && !activeProfile) setActiveProfile(self);
    } catch (e) {
      console.error('Failed to load family members', e);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { loadMembers(); }, [loadMembers]);

  const switchProfile = (profile) => setActiveProfile(profile);

  return (
    <FamilyContext.Provider value={{ members, activeProfile, loading, loadMembers, switchProfile }}>
      {children}
    </FamilyContext.Provider>
  );
}

export const useFamily = () => useContext(FamilyContext);
