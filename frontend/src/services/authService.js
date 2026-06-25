import api from './api';

export const authService = {
  async register(email, password) {
    try {
      const { data } = await api.post('/auth/register', { email, password });
      return data;
    } catch (err) {
      if (!err.response) {
        throw 'Could not connect to the server. Please check if the backend is running.';
      }
      throw err.response?.data?.detail || 'Registration failed';
    }
  },

  async login(email, password) {
    try {
      const { data } = await api.post('/auth/login', { email, password });
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));
      return data;
    } catch (err) {
      if (!err.response) {
        throw 'Could not connect to the server. Please check if the backend is running.';
      }
      throw err.response?.data?.detail || 'Login failed';
    }
  },

  async logout() {
    try {
      await api.post('/auth/logout');
    } catch (_) { /* non-fatal */ }
    finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
    }
  },

  async getMe() {
    try {
      const { data } = await api.get('/auth/me');
      return data;
    } catch (err) {
      if (!err.response) {
        throw 'Could not connect to the server. Please check if the backend is running.';
      }
      throw err.response?.data?.detail || 'Could not fetch user';
    }
  },

  getCurrentUser() {
    try {
      return JSON.parse(localStorage.getItem('user'));
    } catch { return null; }
  },

  isAuthenticated() {
    return !!localStorage.getItem('access_token');
  },

  async forgotPassword(email) {
    try {
      const { data } = await api.post('/auth/forgot-password', { email });
      return data;
    } catch (err) {
      throw err.response?.data?.detail || 'Could not send OTP';
    }
  },

  async verifyOtp(email, otp) {
    try {
      const { data } = await api.post('/auth/verify-otp', { email, otp_code: otp });
      return data;
    } catch (err) {
      throw err.response?.data?.detail || 'Invalid or expired OTP';
    }
  },

  async resetPassword(email, otp, newPassword) {
    try {
      const { data } = await api.post('/auth/reset-password', { email, otp_code: otp, new_password: newPassword });
      return data;
    } catch (err) {
      throw err.response?.data?.detail || 'Password reset failed';
    }
  },
};
