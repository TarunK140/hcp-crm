import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

export const interactionApi = {
  create: (data) => client.post('/interactions', data).then((r) => r.data),
  list: () => client.get('/interactions').then((r) => r.data),
  get: (id) => client.get(`/interactions/${id}`).then((r) => r.data),
  update: (id, data) => client.put(`/interactions/${id}`, data).then((r) => r.data),
  remove: (id) => client.delete(`/interactions/${id}`),
};

export const chatApi = {
  send: (message, currentInteractionId, conversationHistory) =>
    client
      .post('/chat', {
        message,
        current_interaction_id: currentInteractionId ?? null,
        conversation_history: conversationHistory ?? [],
      })
      .then((r) => r.data),
};

export default client;
