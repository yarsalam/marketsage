import axios from 'axios';

// Production should use a same-origin reverse-proxy path. Local development may
// point to http://localhost:4500. The session is an HttpOnly cookie, never JS storage.
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? '';

const axiosInstance = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (typeof window !== 'undefined' && error.response?.status === 401) {
      if (window.location.pathname !== '/auth/login') {
        window.location.assign('/auth/login');
      }
    }
    return Promise.reject(error);
  },
);

export default axiosInstance;
