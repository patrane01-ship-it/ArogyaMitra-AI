import api from './api';

export const getSubscription = async () => {
  const res = await api.get('/api/subscription/');
  return res.data;
};

export const createOrder = async (tier, amountPaise) => {
  const res = await api.post('/api/subscription/order', { tier, amount_paise: amountPaise });
  return res.data;
};

export const verifyPayment = async (orderId, paymentId, signature, tier) => {
  const res = await api.post('/api/subscription/verify', {
    order_id: orderId,
    payment_id: paymentId,
    signature,
    tier,
  });
  return res.data;
};
