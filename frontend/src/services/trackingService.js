import api from './api';

export const trackingService = {
  async accessDocument(token, password) {
    try {
      const { data } = await api.post('/view-api/access', { token, password });
      return data;
    } catch (err) {
      throw err.response?.data?.detail || 'Access denied';
    }
  },

  async trackAction(token, action, sessionDuration = null) {
    try {
      await api.post('/view-api/track', { token, action, session_duration: sessionDuration });
    } catch { /* non-fatal */ }
  },

  async recordWarning(token) {
    try {
      const { data } = await api.post('/security/warn', { token });
      return data;
    } catch (err) {
      throw err.response?.data?.detail || 'Could not record warning';
    }
  },

  async getSecurityStatus(token) {
    try {
      const { data } = await api.get(`/security/status/${token}`);
      return data;
    } catch (err) {
      throw err.response?.data?.detail || 'Could not get security status';
    }
  },

  async detectLeak(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await api.post('/leak/detect', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return data;
    } catch (err) {
      throw err.response?.data?.detail || 'Leak detection failed';
    }
  },

  async analyzeDocument(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await api.post('/leak/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return data;
    } catch (err) {
      throw err.response?.data?.detail || 'Comprehensive analysis failed';
    }
  },

  async analyzeUrl(url) {
    try {
      const { data } = await api.post('/leak/analyze-url', { url });
      return data;
    } catch (err) {
      throw err.response?.data?.detail || 'URL analysis failed';
    }
  },

  async getActivityLogs(docId) {
    try {
      const { data } = await api.get(`/activity/${docId}`);
      return data;
    } catch (err) {
      throw err.response?.data?.detail || 'Could not load activity logs';
    }
  },
};
