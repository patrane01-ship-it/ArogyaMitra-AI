import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { loginUser, registerUser, logoutUser, refreshTokenReq, setAccessToken, clearAccessToken } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  const setAuth = useCallback((accessToken, userData) => {
    setToken(accessToken);
    setUser(userData);
    setAccessToken(accessToken);
  }, []);

  const clearAuth = useCallback(() => {
    setToken(null);
    setUser(null);
    clearAccessToken();
  }, []);

  const refreshToken = useCallback(async () => {
    try {
      const data = await refreshTokenReq();
      if (data?.access_token) {
        setAuth(data.access_token, data.user || {});
        return true;
      }
    } catch {
      clearAuth();
    }
    return false;
  }, [setAuth, clearAuth]);

  useEffect(() => {
    refreshToken().finally(() => setLoading(false));
  }, []);

  // Listen for forced logout (e.g. 401 loop)
  useEffect(() => {
    const handler = () => clearAuth();
    window.addEventListener('arogya:logout', handler);
    return () => window.removeEventListener('arogya:logout', handler);
  }, [clearAuth]);

  const login = async (email, password) => {
    const data = await loginUser(email, password);
    setAuth(data.access_token, data.user || { email });
    return data;
  };

  const register = async (email, password, full_name) => {
    const data = await registerUser(email, password, full_name);
    setAuth(data.access_token, data.user || { email, full_name });
    return data;
  };

  const logout = async () => {
    try { await logoutUser(); } catch {}
    clearAuth();
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, refreshToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
