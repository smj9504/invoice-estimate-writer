import { apiClient } from '../api/config';
import { Company, ApiResponse } from '../types';

export const companyService = {
  // Get all companies
  async getCompanies(): Promise<Company[]> {
    const response = await apiClient.get<ApiResponse<Company[]>>('/companies');
    return response.data.data || [];
  },

  // Get single company
  async getCompany(id: string): Promise<Company> {
    const response = await apiClient.get<ApiResponse<Company>>(`/companies/${id}`);
    if (!response.data.data) {
      throw new Error('Company not found');
    }
    return response.data.data;
  },

  // Create new company
  async createCompany(company: Omit<Company, 'id' | 'created_at' | 'updated_at'>): Promise<Company> {
    const response = await apiClient.post<ApiResponse<Company>>('/companies', company);
    if (!response.data.data) {
      throw new Error('Failed to create company');
    }
    return response.data.data;
  },

  // Update company
  async updateCompany(id: string, company: Partial<Company>): Promise<Company> {
    const response = await apiClient.put<ApiResponse<Company>>(`/companies/${id}`, company);
    if (!response.data.data) {
      throw new Error('Failed to update company');
    }
    return response.data.data;
  },

  // Delete company
  async deleteCompany(id: string): Promise<void> {
    await apiClient.delete(`/companies/${id}`);
  },

  // Upload company logo
  async uploadLogo(id: string, file: File): Promise<string> {
    const formData = new FormData();
    formData.append('logo', file);
    
    const response = await apiClient.post<ApiResponse<{ url: string }>>(`/companies/${id}/logo`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    if (!response.data.data?.url) {
      throw new Error('Failed to upload logo');
    }
    return response.data.data.url;
  },
};