import axios from 'axios';

// API Base URL - will be replaced with environment variable
// Use empty string to use relative URLs (for proxy to work)
const API_BASE_URL = process.env.REACT_APP_API_URL || '';

console.log('API Base URL configured:', API_BASE_URL || 'Using relative URLs (proxy mode)'); // Debug log

// Create axios instance with default config
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds timeout
});

// Request interceptor for auth token
apiClient.interceptors.request.use(
  (config) => {
    // Force relative URLs to use proxy
    if (config.url && !config.url.startsWith('http')) {
      console.log('Making request to:', config.url); // Debug log
      console.log('Using proxy for relative URL'); // Debug log
    }
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);