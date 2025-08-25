// Company Types
export interface Company {
  id: string;
  name: string;
  address: string;
  city: string;
  state: string;
  zipcode?: string;
  phone?: string;
  email?: string;
  logo?: string; // Base64 encoded logo or URL
  company_code?: string; // 4-character unique code
  created_at?: string;
  updated_at?: string;
}

export interface CompanyFormData {
  name: string;
  address: string;
  city: string;
  state: string;
  zipcode?: string;
  phone?: string;
  email?: string;
  logo?: string;
  company_code?: string;
}

export interface CompanyFilter {
  search?: string;
  city?: string;
  state?: string;
}

// Document Types
export type DocumentType = 'estimate' | 'invoice' | 'insurance_estimate' | 'plumber_report';
export type DocumentStatus = 'draft' | 'sent' | 'paid' | 'cancelled';

export interface Document {
  id: string;
  type: DocumentType;
  document_number: string;
  company_id: string;
  client_name: string;
  client_email?: string;
  client_phone?: string;
  client_address?: string;
  status: DocumentStatus;
  total_amount: number;
  created_at: string;
  updated_at: string;
  items?: DocumentItem[];
}

export interface DocumentItem {
  id: string;
  document_id: string;
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
  unit?: string;
  order?: number;
}

// Filter Types
export interface DocumentFilter {
  type?: DocumentType;
  status?: DocumentStatus;
  company_id?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
}

// Room and Floor Plan Types (for insurance estimates)
export interface Room {
  id: string;
  name: string;
  width: number;
  length: number;
  height: number;
  area: number;
  items?: RoomItem[];
}

export interface RoomItem {
  description: string;
  quantity: number;
  unit: string;
  rate: number;
  amount: number;
}

// Work Order Types
export interface WorkOrder {
  id: string;
  work_order_number: string;
  company_id: string;
  document_type: DocumentType;
  client_name: string;
  client_phone?: string;
  client_email?: string;
  client_address?: string;
  client_city?: string;
  client_state?: string;
  client_zipcode?: string;
  trades: string[];
  work_description?: string;
  consultation_notes?: string;
  base_cost: number;
  credits_applied: number;
  final_cost: number;
  cost_override?: number;
  status: 'draft' | 'pending' | 'approved' | 'in_progress' | 'completed' | 'cancelled';
  created_by_staff_id?: string;
  created_by_staff_name?: string;
  assigned_to_staff_id?: string;
  assigned_to_staff_name?: string;
  created_at: string;
  updated_at: string;
  company?: Company;
}

export interface WorkOrderFormData {
  company_id: string;
  document_type: DocumentType;
  client_name: string;
  client_phone?: string;
  client_email?: string;
  client_address?: string;
  client_city?: string;
  client_state?: string;
  client_zipcode?: string;
  trades: string[];
  work_description?: string;
  consultation_notes?: string;
  cost_override?: number;
}

export interface Trade {
  id: string;
  name: string;
  base_cost: number;
  description?: string;
}

export interface Credit {
  id: string;
  company_id: string;
  amount: number;
  description: string;
  expiry_date?: string;
  is_active: boolean;
  created_at: string;
}

export interface CostBreakdown {
  baseCost: number;
  creditsApplied: number;
  finalCost: number;
  availableCredits: number;
}

// API Response Types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];  // Changed from 'data' to match backend
  total: number;
  page: number;
  page_size: number;  // Changed from 'pageSize' to match backend
  total_pages: number;  // Added to match backend
}