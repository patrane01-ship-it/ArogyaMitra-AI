import api from './api';

export const listFamilyMembers = async () => {
  const res = await api.get('/api/family/');
  return res.data;
};

export const addFamilyMember = async (data) => {
  const res = await api.post('/api/family/', data);
  return res.data;
};

export const getFamilyMember = async (profileId) => {
  const res = await api.get(`/api/family/${profileId}`);
  return res.data;
};

export const updateFamilyMember = async (profileId, data) => {
  const res = await api.put(`/api/family/${profileId}`, data);
  return res.data;
};

export const deactivateFamilyMember = async (profileId) => {
  const res = await api.delete(`/api/family/${profileId}`);
  return res.data;
};
