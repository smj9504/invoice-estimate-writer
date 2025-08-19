import { apiClient } from '../api/config';
import { Document, DocumentFilter, ApiResponse, PaginatedResponse } from '../types';

export const documentService = {
  // Get documents with filters
  async getDocuments(filter?: DocumentFilter, page = 1, pageSize = 20): Promise<PaginatedResponse<Document>> {
    const params = {
      ...filter,
      page,
      pageSize,
    };
    
    const response = await apiClient.get<PaginatedResponse<Document>>('/documents', { params });
    return response.data;
  },

  // Get single document
  async getDocument(id: string): Promise<Document> {
    const response = await apiClient.get<ApiResponse<Document>>(`/documents/${id}`);
    if (!response.data.data) {
      throw new Error('Document not found');
    }
    return response.data.data;
  },

  // Create new document
  async createDocument(document: Partial<Document>): Promise<Document> {
    const response = await apiClient.post<ApiResponse<Document>>('/documents', document);
    if (!response.data.data) {
      throw new Error('Failed to create document');
    }
    return response.data.data;
  },

  // Update document
  async updateDocument(id: string, document: Partial<Document>): Promise<Document> {
    const response = await apiClient.put<ApiResponse<Document>>(`/documents/${id}`, document);
    if (!response.data.data) {
      throw new Error('Failed to update document');
    }
    return response.data.data;
  },

  // Delete document
  async deleteDocument(id: string): Promise<void> {
    await apiClient.delete(`/documents/${id}`);
  },

  // Generate PDF
  async generatePDF(id: string): Promise<Blob> {
    const response = await apiClient.get(`/documents/${id}/pdf`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Send document via email
  async sendDocument(id: string, email: string): Promise<void> {
    await apiClient.post(`/documents/${id}/send`, { email });
  },

  // Duplicate document
  async duplicateDocument(id: string): Promise<Document> {
    const response = await apiClient.post<ApiResponse<Document>>(`/documents/${id}/duplicate`);
    if (!response.data.data) {
      throw new Error('Failed to duplicate document');
    }
    return response.data.data;
  },

  // Export documents to Excel
  async exportToExcel(filter?: DocumentFilter): Promise<Blob> {
    const response = await apiClient.post('/documents/export', filter, {
      responseType: 'blob',
    });
    return response.data;
  },
};