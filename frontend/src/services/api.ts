// frontend/src/services/api.ts
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to attach the JWT token automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authService = {
  async login(formData: FormData) {
    // Note: FastAPI expects form-data for login
    const response = await api.post('/auth/jwt/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async register(data: any) {
    const response = await api.post('/auth/register', data);
    return response.data;
  },
  
  logout() {
    localStorage.removeItem('access_token');
  }
};

export const reportService = {
  async analyze(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/analysis/analyze-report', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
};

export default api;