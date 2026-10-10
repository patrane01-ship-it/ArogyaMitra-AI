import api from './api';

export const runPrediction = async (paramName, profileId = null) => {
  const res = await api.post('/api/predictions/run', {
    param_name: paramName,
    profile_id: profileId,
  });
  return res.data;
};

export const getLatestPrediction = async (paramName, profileId = null) => {
  const params = profileId ? `?profile_id=${profileId}` : '';
  const res = await api.get(`/api/predictions/${encodeURIComponent(paramName)}${params}`);
  return res.data;
};

export const listPredictions = async (profileId = null) => {
  const params = profileId ? `?profile_id=${profileId}` : '';
  const res = await api.get(`/api/predictions/${params}`);
  return res.data;
};
