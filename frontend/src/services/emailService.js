import api from './api';

const BASE_URL = import.meta.env.VITE_API_URL || '';

export const emailService = {
  async sendEmails(docId, recipients, duration = { hrs: 24, mins: 0, secs: 0 }) {
    try {
      const payload = {
        recipients,
        duration_hrs: duration.hrs,
        duration_mins: duration.mins,
        duration_secs: duration.secs
      };
      const { data } = await api.post(`/emails/send/${docId}`, payload);
      return data;
    } catch (err) {
      throw err.response?.data?.detail || 'Failed to send emails';
    }
  },

  async uploadRecipients(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await api.post('/emails/upload-recipients', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return data;
    } catch (err) {
      throw err.response?.data?.detail || 'Failed to parse recipients file';
    }
  },

  async getEmailLogs(docId) {
    try {
      const { data } = await api.get(`/emails/logs/${docId}`);
      return data;
    } catch (err) {
      throw err.response?.data?.detail || 'Could not load email logs';
    }
  },
};

export const progressService = {
  async getProgress(docId) {
    try {
      const { data } = await api.get(`/progress/${docId}`);
      return data;
    } catch (err) {
      throw err.response?.data?.detail || 'Could not load progress';
    }
  },

  subscribeToProgress(docId, onData, onDone, onError) {
    const token = localStorage.getItem('access_token');
    const url = `${BASE_URL}/progress/stream/${docId}`;
    const evtSource = new EventSource(url + `?token=${token}`);

    evtSource.onmessage = (e) => {
      try {
        const parsed = JSON.parse(e.data);
        if (parsed.error) { onError?.(parsed.error); evtSource.close(); return; }
        onData(parsed);
        if (parsed.pending === 0 && parsed.in_progress === 0) {
          evtSource.close();
          onDone?.();
        }
      } catch { /* ignore parse errors */ }
    };
    evtSource.onerror = (e) => { onError?.('Connection lost'); evtSource.close(); };
    return () => evtSource.close();
  },
};
