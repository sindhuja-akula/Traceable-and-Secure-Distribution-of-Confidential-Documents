import api from './api';

export const documentService = {
  async createDocument(payload) {
    try {
      const { data } = await api.post('/documents/create', payload);
      return data;
    } catch (err) {
      throw err.response?.data?.detail || 'Document creation failed';
    }
  },

  async uploadDocument(formData) {
    try {
      const { data } = await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return data;
    } catch (err) {
      throw err.response?.data?.detail || 'Document upload failed';
    }
  },

  async listDocuments() {
    try {
      const { data } = await api.get('/documents/');
      return data;
    } catch (err) {
      throw err.response?.data?.detail || 'Could not load documents';
    }
  },

  async getDocument(docId) {
    try {
      const { data } = await api.get(`/documents/${docId}`);
      return data;
    } catch (err) {
      throw err.response?.data?.detail || 'Could not load document';
    }
  },

  async deleteDocument(docId) {
    try {
      await api.delete(`/documents/${docId}`);
    } catch (err) {
      throw err.response?.data?.detail || 'Could not delete document';
    }
  },

  async bulkDeleteDocuments(docIds) {
    try {
      await api.post('/documents/bulk-delete', { doc_ids: docIds });
    } catch (err) {
      throw err.response?.data?.detail || 'Bulk deletion failed';
    }
  },
};
