/**
 * Centralized API Client with Axios.
 * Manages authorization headers with Firebase ID tokens, global error interceptors,
 * and structured endpoint calls.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request Interceptor: Attach Firebase Bearer Token
apiClient.interceptors.request.use(
  async (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Safe error formatting
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      window.dispatchEvent(new Event('auth:unauthorized'));
    }
    const message =
      error.response?.data?.error?.message ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected network error occurred.';
    
    const customError = new Error(message);
    customError.status = error.response?.status;
    customError.code = error.response?.data?.error?.code || 'NETWORK_ERROR';
    customError.details = error.response?.data?.error?.details || null;
    return Promise.reject(customError);
  }
);

export const healthAPI = {
  check: () => apiClient.get('/health'),
};

export const studentsAPI = {
  list: (params) => apiClient.get('/students', { params }),
  get: (studentId) => apiClient.get(`/students/${studentId}`),
  create: (data) => apiClient.post('/students', data),
  update: (studentId, data) => apiClient.put(`/students/${studentId}`, data),
  deactivate: (studentId) => apiClient.delete(`/students/${studentId}`),
  enrollFace: (studentId, payload) => apiClient.post(`/students/${studentId}/enroll-face`, payload),
  deleteFaceTemplate: (studentId) => apiClient.delete(`/students/${studentId}/face-template`),
};

export const recognitionAPI = {
  identify: (payload) => apiClient.post('/recognition/identify', payload),
};

export const attendanceAPI = {
  getDashboard: () => apiClient.get('/dashboard'),
  list: (params) => apiClient.get('/attendance', { params }),
  markManual: (payload) => apiClient.post('/attendance/mark-manual', payload),
  getSummary: (params) => apiClient.get('/attendance/summary', { params }),
  exportCsvUrl: (params) => {
    const query = new URLSearchParams(params).toString();
    return `${API_BASE_URL}/attendance/export?${query}`;
  },
};

export default apiClient;
