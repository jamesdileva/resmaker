import axios from 'axios';

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status: number | undefined = error.response?.status;
    let message = 'An unexpected error occurred';
    if (error.code === 'ECONNABORTED') {
      message = 'Request timed out';
    } else if (status === 404) {
      message = 'Not found';
    } else if (status !== undefined) {
      const detail = error.response?.data;
      message =
        typeof detail?.detail === 'string'
          ? detail.detail
          : `Request failed with status ${status}`;
    }
    return Promise.reject(
      new Error(message, { cause: { status, original: error } }),
    );
  },
);
