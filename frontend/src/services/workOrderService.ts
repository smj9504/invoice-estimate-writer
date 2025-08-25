import api from './api';
import { WorkOrder, WorkOrderFormData, Trade, Credit, CostBreakdown, PaginatedResponse } from '../types';

export const workOrderService = {
  // Work Order operations
  async getWorkOrders(page = 1, pageSize = 10): Promise<PaginatedResponse<WorkOrder>> {
    const response = await api.get('/api/work-orders/', {
      params: { page, page_size: pageSize }
    });
    return response.data;
  },

  async getWorkOrder(id: string): Promise<WorkOrder> {
    const response = await api.get(`/api/work-orders/${id}`);
    return response.data;
  },

  async createWorkOrder(workOrderData: WorkOrderFormData): Promise<WorkOrder> {
    const response = await api.post('/api/work-orders/', workOrderData);
    return response.data;
  },

  async updateWorkOrder(id: string, workOrderData: Partial<WorkOrderFormData>): Promise<WorkOrder> {
    const response = await api.patch(`/api/work-orders/${id}`, workOrderData);
    return response.data;
  },

  async deleteWorkOrder(id: string): Promise<void> {
    await api.delete(`/api/work-orders/${id}`);
  },

  // Generate new work order number
  async generateWorkOrderNumber(): Promise<{ work_order_number: string }> {
    const response = await api.get('/api/work-orders/generate-number');
    return response.data;
  },

  // Trade operations
  async getTrades(): Promise<Trade[]> {
    const response = await api.get('/api/trades/');
    return response.data;
  },

  // Credit operations
  async getCustomerCredits(companyId: string): Promise<Credit[]> {
    const response = await api.get(`/api/credits/customer/${companyId}`);
    return response.data;
  },

  async getAvailableCredits(companyId: string): Promise<Credit[]> {
    const response = await api.get(`/api/credits/customer/${companyId}`, {
      params: { active_only: true }
    });
    return response.data;
  },

  // Cost calculation
  async calculateCost(data: {
    document_type: string;
    trades: string[];
    company_id: string;
  }): Promise<CostBreakdown> {
    const response = await api.post('/api/work-orders/calculate-cost', data);
    return response.data;
  },

  // Document type operations
  async getDocumentTypes(): Promise<{ id: string; name: string; base_cost: number }[]> {
    const response = await api.get('/api/document-types/');
    return response.data;
  },

  // PDF Generation (if needed)
  async previewPDF(workOrderData: any): Promise<Blob> {
    const response = await api.post('/api/work-orders/preview-pdf', workOrderData, {
      responseType: 'blob',
      headers: {
        'Accept': 'application/pdf',
      },
    });
    return response.data;
  },

  // Search and filter
  async searchWorkOrders(params: {
    search?: string;
    company_id?: string;
    document_type?: string;
    status?: string;
    date_from?: string;
    date_to?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<WorkOrder>> {
    const response = await api.get('/api/work-orders/', { params });
    return response.data;
  },

  // Status updates
  async updateWorkOrderStatus(id: string, status: WorkOrder['status']): Promise<WorkOrder> {
    const response = await api.patch(`/api/work-orders/${id}`, { status });
    return response.data;
  },

  // Mock data for development (can be removed when backend is ready)
  getMockTrades(): Trade[] {
    return [
      { id: '1', name: 'Plumbing', base_cost: 150, description: 'General plumbing work' },
      { id: '2', name: 'Electrical', base_cost: 200, description: 'Electrical installations and repairs' },
      { id: '3', name: 'HVAC', base_cost: 300, description: 'Heating, ventilation, and air conditioning' },
      { id: '4', name: 'Carpentry', base_cost: 120, description: 'Carpentry and woodwork' },
      { id: '5', name: 'Painting', base_cost: 80, description: 'Interior and exterior painting' },
      { id: '6', name: 'Roofing', base_cost: 400, description: 'Roof repairs and installation' },
      { id: '7', name: 'Flooring', base_cost: 250, description: 'Floor installation and repair' },
      { id: '8', name: 'Drywall', base_cost: 100, description: 'Drywall installation and repair' }
    ];
  },

  getMockDocumentTypes() {
    return [
      { id: 'estimate', name: 'Estimate', base_cost: 50 },
      { id: 'invoice', name: 'Invoice', base_cost: 0 },
      { id: 'insurance_estimate', name: 'Insurance Estimate', base_cost: 100 },
      { id: 'plumber_report', name: 'Plumber\'s Report', base_cost: 200 }
    ];
  }
};

export default workOrderService;