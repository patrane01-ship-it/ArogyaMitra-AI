import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor for logging or auth header enrichment
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const errorMsg = error.response?.data?.message || error.message || 'An error occurred';
    console.error('[API Error]:', errorMsg, error.response?.data);
    return Promise.reject(error);
  }
);

// Records API
export const uploadRecordFile = async (formData) => {
  const response = await api.post('/api/records/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const createManualRecord = async (payload) => {
  const response = await api.post('/api/records/manual', payload);
  return response.data;
};

export const getRecords = async (skip = 0, limit = 50) => {
  const response = await api.get(`/api/records/?skip=${skip}&limit=${limit}`);
  return response.data;
};

export const getRecordById = async (recordId) => {
  const response = await api.get(`/api/records/${recordId}`);
  return response.data;
};

export const downloadRecord = async (recordId) => {
  const response = await api.get(`/api/records/${recordId}/download`, {
    responseType: 'blob',
  });
  return response.data;
};

export const updateRecord = async (recordId, data) => {
  const response = await api.put(`/api/records/${recordId}`, data);
  return response.data;
};

export const deleteRecord = async (recordId) => {
  const response = await api.delete(`/api/records/${recordId}`);
  return response.data;
};

// Clinical Parameters API
export const getLatestParams = async () => {
  const response = await api.get('/api/params/');
  return response.data;
};

export const getParamHistory = async (paramName) => {
  const response = await api.get(`/api/params/${encodeURIComponent(paramName)}`);
  return response.data;
};

export const updateParam = async (paramId, data) => {
  const response = await api.put(`/api/params/${paramId}`, data);
  return response.data;
};

// Risk API
export const getCurrentRisk = async () => {
  const response = await api.get('/api/risk/current');
  return response.data;
};

export const getRiskHistory = async (limit = 20) => {
  const response = await api.get(`/api/risk/history?limit=${limit}`);
  return response.data;
};

export const recomputeRisk = async () => {
  const response = await api.post('/api/risk/recompute');
  return response.data;
};

// Reminders API
export const getReminders = async (includeAcknowledged = false) => {
  const response = await api.get(`/api/reminders/?include_acknowledged=${includeAcknowledged}`);
  return response.data;
};

export const createReminder = async (data) => {
  const response = await api.post('/api/reminders/', data);
  return response.data;
};

export const updateReminder = async (reminderId, data) => {
  const response = await api.put(`/api/reminders/${reminderId}`, data);
  return response.data;
};

export const acknowledgeReminder = async (reminderId) => {
  const response = await api.patch(`/api/reminders/${reminderId}/ack`);
  return response.data;
};

export const deleteReminder = async (reminderId) => {
  const response = await api.delete(`/api/reminders/${reminderId}`);
  return response.data;
};

// Doctor Report API
export const generateDoctorReport = async () => {
  const response = await api.post('/api/report/generate');
  return response.data;
};

export const getLatestReport = async () => {
  const response = await api.get('/api/report/latest');
  return response.data;
};

export const downloadReportPdf = async (reportId) => {
  const response = await api.get(`/api/report/${reportId}/pdf`, {
    responseType: 'blob',
  });
  return response.data;
};

export const generateShareLink = async (reportId, expiryHours = 24) => {
  const response = await api.post(`/api/report/${reportId}/share?expiry_hours=${expiryHours}`);
  return response.data;
};

// Public Share API
export const getSharedResource = async (token) => {
  const response = await api.get(`/share/${token}`);
  return response.data;
};

export default api;
