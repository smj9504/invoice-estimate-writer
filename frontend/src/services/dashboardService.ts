import api from './api';

export interface DashboardStats {
  total_work_orders: number;
  revenue_this_month: number;
  revenue_last_month: number;
  pending_approvals: number;
  active_work_orders: number;
  completion_rate: number;
  average_processing_time: number; // in days
  revenue_trend: number; // percentage change
}

export interface RevenueData {
  date: string;
  revenue: number;
  work_orders: number;
}

export interface StatusDistribution {
  status: string;
  count: number;
  percentage: number;
}

export interface DocumentTypeDistribution {
  document_type: string;
  count: number;
  revenue: number;
}

export interface RecentActivity {
  id: string;
  type: 'work_order_created' | 'status_changed' | 'payment_received' | 'staff_activity';
  title: string;
  description: string;
  timestamp: string;
  work_order_number?: string;
  staff_name?: string;
  amount?: number;
}

export interface StaffPerformance {
  staff_id: string;
  staff_name: string;
  completed_orders: number;
  revenue_generated: number;
  average_completion_time: number;
  rating: number;
}

export interface CompanyRanking {
  company_id: string;
  company_name: string;
  total_orders: number;
  total_revenue: number;
  active_orders: number;
  last_order_date: string;
}

export interface TradePopularity {
  trade_name: string;
  count: number;
  revenue: number;
  trend: 'up' | 'down' | 'stable';
}

export interface CreditUsage {
  total_credits_issued: number;
  credits_used: number;
  credits_remaining: number;
  utilization_rate: number;
}

export interface Alert {
  id: string;
  type: 'overdue' | 'low_credit' | 'payment_failed' | 'system_issue';
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: string;
  work_order_id?: string;
  company_id?: string;
}

export interface DashboardData {
  stats: DashboardStats;
  revenue_chart: RevenueData[];
  status_distribution: StatusDistribution[];
  document_type_distribution: DocumentTypeDistribution[];
  recent_activities: RecentActivity[];
  staff_performance: StaffPerformance[];
  company_rankings: CompanyRanking[];
  trade_popularity: TradePopularity[];
  credit_usage: CreditUsage;
  alerts: Alert[];
}

export interface DashboardFilters {
  date_from?: string;
  date_to?: string;
  company_id?: string;
  refresh?: boolean;
}

export const dashboardService = {
  // Get complete dashboard data
  async getDashboardData(filters?: DashboardFilters): Promise<DashboardData> {
    try {
      const overviewResponse = await api.get('/api/dashboard/overview', { params: filters });
      const revenueResponse = await api.get('/api/dashboard/revenue', { params: { ...filters, period_type: 'month' } });
      const companiesResponse = await api.get('/api/dashboard/companies', { params: { limit: 10 } });
      const creditsResponse = await api.get('/api/dashboard/credits');
      
      const overview = overviewResponse.data;
      const revenueData = revenueResponse.data;
      const companies = companiesResponse.data;
      const credits = creditsResponse.data;
      
      // Transform backend data to frontend format
      const transformedRevenueData = this.transformRevenueData(revenueData);
      const transformedDocumentTypes = this.transformDocumentTypes(revenueData);
      
      return {
        stats: {
          total_work_orders: overview.work_order_metrics.total_leads + overview.work_order_metrics.active_orders + overview.work_order_metrics.completed_orders,
          revenue_this_month: overview.revenue_current_month,
          revenue_last_month: overview.revenue_previous_month,
          pending_approvals: overview.work_order_metrics.total_leads,
          active_work_orders: overview.work_order_metrics.active_orders,
          completion_rate: 85.2, // Calculate from actual data later
          average_processing_time: 5.2, // Calculate from actual data later
          revenue_trend: overview.revenue_growth_percentage
        },
        revenue_chart: transformedRevenueData,
        status_distribution: this.getMockStatusDistribution(), // TODO: Replace with real data
        document_type_distribution: transformedDocumentTypes,
        recent_activities: overview.recent_activities,
        staff_performance: this.getMockStaffPerformance(), // TODO: Replace with real data
        company_rankings: companies,
        trade_popularity: this.getMockTradePopularity(), // TODO: Replace with real data
        credit_usage: {
          total_credits_issued: credits.total_credits_allocated,
          credits_used: credits.total_credits_used,
          credits_remaining: credits.total_credits_remaining,
          utilization_rate: credits.total_credits_allocated > 0 ? (credits.total_credits_used / credits.total_credits_allocated) * 100 : 0
        },
        alerts: this.getMockAlerts() // TODO: Replace with real data
      };
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      // Fallback to mock data in case of error
      return this.getMockDashboardData();
    }
  },

  // Get key metrics/stats
  async getStats(filters?: DashboardFilters): Promise<DashboardStats> {
    const response = await api.get('/api/dashboard/metrics', { params: filters });
    const metrics = response.data;
    const overview = await api.get('/api/dashboard/overview', { params: filters });
    const overviewData = overview.data;
    
    return {
      total_work_orders: metrics.total_leads + metrics.active_orders + metrics.completed_orders,
      revenue_this_month: overviewData.revenue_current_month,
      revenue_last_month: overviewData.revenue_previous_month,
      pending_approvals: metrics.total_leads,
      active_work_orders: metrics.active_orders,
      completion_rate: 85.2, // TODO: Calculate from actual data
      average_processing_time: 5.2, // TODO: Calculate from actual data
      revenue_trend: overviewData.revenue_growth_percentage
    };
  },

  // Get revenue chart data
  async getRevenueData(filters?: DashboardFilters): Promise<RevenueData[]> {
    const response = await api.get('/api/dashboard/revenue', { 
      params: { 
        ...filters, 
        period_type: 'month'
      } 
    });
    return this.transformRevenueData(response.data);
  },

  // Get work order status distribution
  async getStatusDistribution(filters?: DashboardFilters): Promise<StatusDistribution[]> {
    const response = await api.get('/api/dashboard/status-distribution', { params: filters });
    return response.data;
  },

  // Get document type distribution
  async getDocumentTypeDistribution(filters?: DashboardFilters): Promise<DocumentTypeDistribution[]> {
    const response = await api.get('/api/dashboard/document-type-distribution', { params: filters });
    return response.data;
  },

  // Get recent activities
  async getRecentActivities(limit = 10, filters?: DashboardFilters): Promise<RecentActivity[]> {
    const response = await api.get('/api/dashboard/recent-activities', { 
      params: { ...filters, limit } 
    });
    return response.data;
  },

  // Get staff performance
  async getStaffPerformance(filters?: DashboardFilters): Promise<StaffPerformance[]> {
    const response = await api.get('/api/dashboard/staff-performance', { params: filters });
    return response.data;
  },

  // Get company rankings
  async getCompanyRankings(limit = 10, filters?: DashboardFilters): Promise<CompanyRanking[]> {
    const response = await api.get('/api/dashboard/company-rankings', { 
      params: { ...filters, limit } 
    });
    return response.data;
  },

  // Get trade popularity
  async getTradePopularity(filters?: DashboardFilters): Promise<TradePopularity[]> {
    const response = await api.get('/api/dashboard/trade-popularity', { params: filters });
    return response.data;
  },

  // Get credit usage statistics
  async getCreditUsage(filters?: DashboardFilters): Promise<CreditUsage> {
    const response = await api.get('/api/dashboard/credit-usage', { params: filters });
    return response.data;
  },

  // Get system alerts
  async getAlerts(filters?: DashboardFilters): Promise<Alert[]> {
    const response = await api.get('/api/dashboard/alerts', { params: filters });
    return response.data;
  },

  // Bulk operations
  async approveMultipleOrders(workOrderIds: string[]): Promise<{ success: boolean; message: string }> {
    const response = await api.post('/api/work-orders/bulk-approve', { work_order_ids: workOrderIds });
    return response.data;
  },

  // Export reports
  async exportReport(
    type: 'excel' | 'pdf', 
    filters?: DashboardFilters
  ): Promise<Blob> {
    const response = await api.post('/api/dashboard/export', 
      { type, ...filters }, 
      { responseType: 'blob' }
    );
    return response.data;
  },

  // System refresh
  async refreshDashboard(): Promise<{ success: boolean; message: string }> {
    const response = await api.post('/api/dashboard/refresh');
    return response.data;
  },

  // Mock data for development (remove when backend is ready)
  getMockDashboardData(): DashboardData {
    return {
      stats: {
        total_work_orders: 156,
        revenue_this_month: 125000,
        revenue_last_month: 98000,
        pending_approvals: 12,
        active_work_orders: 34,
        completion_rate: 85.2,
        average_processing_time: 5.2,
        revenue_trend: 27.5
      },
      revenue_chart: this.getMockRevenueData(),
      status_distribution: this.getMockStatusDistribution(),
      document_type_distribution: this.getMockDocumentTypeDistribution(),
      recent_activities: this.getMockRecentActivities(),
      staff_performance: this.getMockStaffPerformance(),
      company_rankings: this.getMockCompanyRankings(),
      trade_popularity: this.getMockTradePopularity(),
      credit_usage: this.getMockCreditUsage(),
      alerts: this.getMockAlerts()
    };
  },

  getMockRevenueData(): RevenueData[] {
    const data: RevenueData[] = [];
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);

    for (let i = 0; i < 30; i++) {
      const date = new Date(startDate);
      date.setDate(startDate.getDate() + i);
      
      data.push({
        date: date.toISOString().split('T')[0],
        revenue: Math.floor(Math.random() * 10000) + 2000,
        work_orders: Math.floor(Math.random() * 8) + 1
      });
    }
    return data;
  },

  getMockStatusDistribution(): StatusDistribution[] {
    return [
      { status: 'pending', count: 12, percentage: 15.2 },
      { status: 'approved', count: 28, percentage: 35.4 },
      { status: 'in_progress', count: 34, percentage: 43.0 },
      { status: 'completed', count: 5, percentage: 6.3 }
    ];
  },

  getMockDocumentTypeDistribution(): DocumentTypeDistribution[] {
    return [
      { document_type: 'estimate', count: 45, revenue: 67500 },
      { document_type: 'invoice', count: 38, revenue: 82000 },
      { document_type: 'insurance_estimate', count: 22, revenue: 45000 },
      { document_type: 'plumber_report', count: 15, revenue: 28500 }
    ];
  },

  getMockRecentActivities(): RecentActivity[] {
    return [
      {
        id: '1',
        type: 'work_order_created',
        title: 'New Work Order Created',
        description: 'Work order #WO-2025-001 created for ABC Company',
        timestamp: new Date(Date.now() - 300000).toISOString(), // 5 min ago
        work_order_number: 'WO-2025-001',
        staff_name: 'John Smith'
      },
      {
        id: '2',
        type: 'status_changed',
        title: 'Status Updated',
        description: 'Work order #WO-2025-002 marked as completed',
        timestamp: new Date(Date.now() - 600000).toISOString(), // 10 min ago
        work_order_number: 'WO-2025-002',
        staff_name: 'Jane Doe'
      },
      {
        id: '3',
        type: 'payment_received',
        title: 'Payment Received',
        description: 'Payment of $2,500 received for work order #WO-2024-156',
        timestamp: new Date(Date.now() - 900000).toISOString(), // 15 min ago
        amount: 2500,
        work_order_number: 'WO-2024-156'
      }
    ];
  },

  getMockStaffPerformance(): StaffPerformance[] {
    return [
      { staff_id: '1', staff_name: 'John Smith', completed_orders: 28, revenue_generated: 45000, average_completion_time: 4.2, rating: 4.8 },
      { staff_id: '2', staff_name: 'Jane Doe', completed_orders: 22, revenue_generated: 38000, average_completion_time: 5.1, rating: 4.6 },
      { staff_id: '3', staff_name: 'Mike Johnson', completed_orders: 19, revenue_generated: 32000, average_completion_time: 6.0, rating: 4.4 }
    ];
  },

  getMockCompanyRankings(): CompanyRanking[] {
    return [
      { 
        company_id: '1', 
        company_name: 'ABC Construction', 
        total_orders: 45, 
        total_revenue: 125000, 
        active_orders: 8,
        last_order_date: new Date(Date.now() - 86400000).toISOString()
      },
      { 
        company_id: '2', 
        company_name: 'XYZ Plumbing', 
        total_orders: 32, 
        total_revenue: 87000, 
        active_orders: 6,
        last_order_date: new Date(Date.now() - 172800000).toISOString()
      }
    ];
  },

  getMockTradePopularity(): TradePopularity[] {
    return [
      { trade_name: 'Plumbing', count: 45, revenue: 67500, trend: 'up' },
      { trade_name: 'Electrical', count: 38, revenue: 76000, trend: 'stable' },
      { trade_name: 'HVAC', count: 28, revenue: 84000, trend: 'up' },
      { trade_name: 'Carpentry', count: 22, revenue: 33000, trend: 'down' }
    ];
  },

  getMockCreditUsage(): CreditUsage {
    return {
      total_credits_issued: 10000,
      credits_used: 7500,
      credits_remaining: 2500,
      utilization_rate: 75.0
    };
  },

  getMockAlerts(): Alert[] {
    return [
      {
        id: '1',
        type: 'overdue',
        title: 'Overdue Work Orders',
        description: '3 work orders are overdue and require immediate attention',
        severity: 'high',
        timestamp: new Date().toISOString()
      },
      {
        id: '2',
        type: 'low_credit',
        title: 'Low Credit Warning',
        description: 'Company ABC Construction has less than 100 credits remaining',
        severity: 'medium',
        timestamp: new Date().toISOString(),
        company_id: '1'
      }
    ];
  },

  // Transform backend revenue data to frontend format
  transformRevenueData(backendData: any[]): RevenueData[] {
    if (!Array.isArray(backendData) || backendData.length === 0) {
      return this.getMockRevenueData();
    }

    return backendData.map(period => ({
      date: period.start_date ? new Date(period.start_date).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
      revenue: Number(period.net_revenue || 0),
      work_orders: Object.values(period.document_counts || {}).reduce((sum: number, count: any) => sum + Number(count), 0)
    }));
  },

  // Transform backend document type data to frontend format
  transformDocumentTypes(backendData: any[]): DocumentTypeDistribution[] {
    if (!Array.isArray(backendData) || backendData.length === 0) {
      return this.getMockDocumentTypeDistribution();
    }

    const result: DocumentTypeDistribution[] = [];
    backendData.forEach((period: any) => {
      if (period.document_counts && typeof period.document_counts === 'object') {
        const documentCounts = period.document_counts as Record<string, any>;
        const totalCounts = Object.values(documentCounts).reduce((sum: number, c: any) => sum + Number(c), 0);
        
        Object.entries(documentCounts).forEach(([docType, count]: [string, any]) => {
          const existing = result.find(item => item.document_type === docType);
          const proportionalRevenue = totalCounts > 0 ? Number(period.total_revenue || 0) * (Number(count) / totalCounts) : 0;
          
          if (existing) {
            existing.count += Number(count);
            existing.revenue += proportionalRevenue;
          } else {
            result.push({
              document_type: docType,
              count: Number(count),
              revenue: proportionalRevenue
            });
          }
        });
      }
    });

    return result.length > 0 ? result : this.getMockDocumentTypeDistribution();
  }
};

export default dashboardService;