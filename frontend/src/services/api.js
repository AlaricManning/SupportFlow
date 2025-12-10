import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const ticketService = {
  createTicket: async (ticketData) => {
    const response = await api.post('/api/tickets', ticketData);
    return response.data;
  },

  getTickets: async (statusFilter = null) => {
    const params = statusFilter ? { status_filter: statusFilter } : {};
    const response = await api.get('/api/tickets', { params });
    return response.data;
  },

  getTicket: async (ticketId) => {
    const response = await api.get(`/api/tickets/${ticketId}`);
    return response.data;
  },

  getTicketByNumber: async (ticketNumber) => {
    const response = await api.get(`/api/tickets/number/${ticketNumber}`);
    return response.data;
  },

  updateTicket: async (ticketId, updateData) => {
    const response = await api.patch(`/api/tickets/${ticketId}`, updateData);
    return response.data;
  },

  deleteTicket: async (ticketId) => {
    await api.delete(`/api/tickets/${ticketId}`);
  },
};

export const statsService = {
  getStats: async () => {
    const response = await api.get('/api/stats');
    return response.data;
  },
};

export default api;
