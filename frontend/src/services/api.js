import axios from 'axios';

// ── In-memory token store (NEVER in localStorage) ────────────
let _accessToken = null;
export const setAccessToken = (t) => { _accessToken = t; };
export const clearAccessToken = () => { _accessToken = null; };
export const getAccessToken = () => _accessToken;

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true, // needed for httpOnly refresh cookie
});

// Request: inject JWT
api.interceptors.request.use((config) => {
  if (_accessToken) {
    config.headers['Authorization'] = `Bearer ${_accessToken}`;
  }
  return config;
});

// Response: on 401 → refresh once → retry
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const refresh = await axios.post(
          `${import.meta.env.VITE_API_URL || ''}/api/auth/refresh`,
          {},
          { withCredentials: true }
        );
        const newToken = refresh.data?.access_token;
        if (newToken) {
          setAccessToken(newToken);
          original.headers['Authorization'] = `Bearer ${newToken}`;
          return api(original);
        }
      } catch {
        clearAccessToken();
        window.dispatchEvent(new Event('arogya:logout'));
      }
    }
    return Promise.reject(error);
  }
);

// ── Auth ──────────────────────────────────────────────────────
export const loginUser = async (email, password) => {
  const res = await api.post('/api/auth/login', { email, password });
  return res.data;
};

export const registerUser = async (email, password, full_name) => {
  const res = await api.post('/api/auth/register', { email, password, full_name });
  return res.data;
};

export const logoutUser = async () => {
  await api.post('/api/auth/logout');
};

export const refreshTokenReq = async () => {
  const res = await api.post('/api/auth/refresh', {}, { withCredentials: true });
  return res.data;
};

// ── Records ───────────────────────────────────────────────────
export const uploadRecordFile = async (formData, profileId = null) => {
  const url = profileId ? `/api/records/upload?profile_id=${profileId}` : '/api/records/upload';
  const res = await api.post(url, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
  return res.data;
};

export const createManualRecord = async (payload, profileId = null) => {
  const url = profileId ? `/api/records/manual?profile_id=${profileId}` : '/api/records/manual';
  const res = await api.post(url, payload);
  return res.data;
};

export const getRecords = async (skip = 0, limit = 50, profileId = null) => {
  const profileParam = profileId ? `&profile_id=${profileId}` : '';
  const res = await api.get(`/api/records/?skip=${skip}&limit=${limit}${profileParam}`);
  return res.data;
};

export const getRecordById = async (recordId) => {
  const res = await api.get(`/api/records/${recordId}`);
  return res.data;
};

export const downloadRecord = async (recordId) => {
  const res = await api.get(`/api/records/${recordId}/download`, { responseType: 'blob' });
  return res.data;
};

export const updateRecord = async (recordId, data) => {
  const res = await api.put(`/api/records/${recordId}`, data);
  return res.data;
};

export const deleteRecord = async (recordId) => {
  const res = await api.delete(`/api/records/${recordId}`);
  return res.data;
};

// ── Clinical Parameters ───────────────────────────────────────
export const getLatestParams = async (profileId = null) => {
  const p = profileId ? `?profile_id=${profileId}` : '';
  const res = await api.get(`/api/params/${p}`);
  return res.data;
};

export const getParamHistory = async (paramName, profileId = null) => {
  const p = profileId ? `?profile_id=${profileId}` : '';
  const res = await api.get(`/api/params/${encodeURIComponent(paramName)}${p}`);
  return res.data;
};

export const updateParam = async (paramId, data) => {
  const res = await api.put(`/api/params/${paramId}`, data);
  return res.data;
};

// ── Risk ──────────────────────────────────────────────────────
export const getCurrentRisk = async (profileId = null) => {
  const p = profileId ? `?profile_id=${profileId}` : '';
  const res = await api.get(`/api/risk/current${p}`);
  return res.data;
};

export const getRiskHistory = async (limit = 20, profileId = null) => {
  const p = profileId ? `&profile_id=${profileId}` : '';
  const res = await api.get(`/api/risk/history?limit=${limit}${p}`);
  return res.data;
};

export const recomputeRisk = async (profileId = null) => {
  const p = profileId ? `?profile_id=${profileId}` : '';
  const res = await api.post(`/api/risk/recompute${p}`);
  return res.data;
};

// ── Reminders ─────────────────────────────────────────────────
export const getReminders = async (includeAcknowledged = false, profileId = null) => {
  const p = profileId ? `&profile_id=${profileId}` : '';
  const res = await api.get(`/api/reminders/?include_acknowledged=${includeAcknowledged}${p}`);
  return res.data;
};

export const createReminder = async (data, profileId = null) => {
  const p = profileId ? `?profile_id=${profileId}` : '';
  const res = await api.post(`/api/reminders/${p}`, data);
  return res.data;
};

export const updateReminder = async (reminderId, data) => {
  const res = await api.put(`/api/reminders/${reminderId}`, data);
  return res.data;
};

export const acknowledgeReminder = async (reminderId) => {
  const res = await api.patch(`/api/reminders/${reminderId}/ack`);
  return res.data;
};

export const deleteReminder = async (reminderId) => {
  const res = await api.delete(`/api/reminders/${reminderId}`);
  return res.data;
};

// ── Doctor Reports ────────────────────────────────────────────
export const generateDoctorReport = async (profileId = null) => {
  const p = profileId ? `?profile_id=${profileId}` : '';
  const res = await api.post(`/api/report/generate${p}`);
  return res.data;
};

export const getLatestReport = async () => {
  const res = await api.get('/api/report/latest');
  return res.data;
};

export const downloadReportPdf = async (reportId) => {
  const res = await api.get(`/api/report/${reportId}/pdf`, { responseType: 'blob' });
  return res.data;
};

export const generateShareLink = async (reportId, expiryHours = 24) => {
  const res = await api.post(`/api/report/${reportId}/share?expiry_hours=${expiryHours}`);
  return res.data;
};

export const getSharedResource = async (token) => {
  const res = await api.get(`/share/${token}`);
  return res.data;
};

export default api;
