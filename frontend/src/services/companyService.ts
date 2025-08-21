import api from './api';
import { Company, CompanyFormData } from '../types';

export const companyService = {
  // Get all companies with optional filters
  getCompanies: async (search?: string, city?: string, state?: string): Promise<Company[]> => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (city) params.append('city', city);
    if (state) params.append('state', state);
    
    const response = await api.get(`/companies/?${params.toString()}`);
    return response.data.data;
  },

  // Get single company by ID
  getCompany: async (id: string): Promise<Company> => {
    const response = await api.get(`/companies/${id}`);
    return response.data.data;
  },

  // Create new company
  createCompany: async (data: CompanyFormData): Promise<Company> => {
    const response = await api.post('/companies/', data);
    return response.data.data;
  },

  // Update existing company
  updateCompany: async (id: string, data: Partial<CompanyFormData>): Promise<Company> => {
    const response = await api.put(`/companies/${id}`, data);
    return response.data.data;
  },

  // Delete company
  deleteCompany: async (id: string): Promise<void> => {
    console.log('Deleting company with ID:', id);
    const response = await api.delete(`/companies/${id}`);
    console.log('Delete response:', response);
    return response.data;
  },

  // Upload company logo
  uploadLogo: async (companyId: string, file: File): Promise<string> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post(`/companies/${companyId}/logo`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data.logo;
  },
};