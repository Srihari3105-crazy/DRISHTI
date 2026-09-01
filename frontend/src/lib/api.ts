import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor: attach JWT token
api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: auto-refresh on 401
let isRefreshing = false;
let failedQueue: Array<{ resolve: Function; reject: Function }> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) throw new Error('No refresh token');

        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, null, {
          params: { refresh_token: refreshToken },
        });

        const newToken = response.data.access_token;
        localStorage.setItem('access_token', newToken);

        processQueue(null, newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        // Clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;

// ─── API Functions ────────────────────────────────────────────

// Auth
export const authAPI = {
  login: (phone: string, password: string) =>
    api.post('/auth/login', { phone, password }),
  register: (data: {
    name: string;
    phone: string;
    email?: string;
    password: string;
    role: string;
    district_id?: string;
    pincode?: string;
    area?: string;
    state?: string;
  }) => api.post('/auth/register', data),
  refresh: (refreshToken: string) =>
    api.post('/auth/refresh', null, { params: { refresh_token: refreshToken } }),
};

// PIN Code
export const pincodeAPI = {
  lookup: (pincode: string) => api.get(`/pincode/${pincode}`),
};



// Patients
export const patientsAPI = {
  list: (params?: Record<string, any>) => api.get('/patients', { params }),
  get: (id: string) => api.get(`/patients/${id}`),
  create: (data: any) => api.post('/patients', data),
  sendOTP: (id: string, mobile: string) =>
    api.post(`/patients/${id}/verify-mobile`, { mobile }),
  verifyOTP: (id: string, otp: string) =>
    api.post(`/patients/${id}/confirm-mobile`, { otp }),
};

// Screenings
export const screeningsAPI = {
  submit: (data: any) => api.post('/screenings', data),
  get: (id: string) => api.get(`/screenings/${id}`),
};

// Referrals
export const referralsAPI = {
  list: (params?: Record<string, any>) => api.get('/referrals', { params }),
  get: (id: string) => api.get(`/referrals/${id}`),
  getNotifications: (id: string) => api.get(`/referrals/${id}/notifications`),
  assign: (id: string, doctorId: string) =>
    api.post(`/referrals/${id}/assign`, { doctor_id: doctorId }),
  autoAssign: () => api.post('/referrals/auto-assign'),
  schedule: (id: string, data: { scheduled_at: string; hospital_id: string }) =>
    api.post(`/referrals/${id}/schedule`, data),
  markVisited: (id: string, notes?: string) =>
    api.post(`/referrals/${id}/visit`, { notes }),
  requestRetake: (id: string, reason: string) =>
    api.post(`/referrals/${id}/retake`, { reason }),
};

// Doctors
export const doctorsAPI = {
  register: (data: any) => api.post('/doctors/register', data),
  list: (districtId?: string) =>
    api.get('/doctors', { params: districtId ? { district_id: districtId } : {} }),
};

// Officers
export const officersAPI = {
  dashboard: () => api.get('/officers/dashboard'),
  hospitals: (districtId?: string) =>
    api.get('/officers/hospitals', { params: districtId ? { district_id: districtId } : {} }),
};

// Exports
export const exportsAPI = {
  hmisForm1: (month: string) =>
    api.get('/referrals/export/hmis-form1', {
      params: { month },
      responseType: 'blob',
    }),
};
