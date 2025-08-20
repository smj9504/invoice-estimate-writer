// Company Types
export interface Company {
  id: string;
  name: string;
  address: string;
  city: string;
  state: string;
  zip?: string;
  phone?: string;
  email?: string;
  logo?: string; // Base64 encoded logo or URL
  created_at?: string;
  updated_at?: string;
}

export interface CompanyFormData {
  name: string;
  address: string;
  city: string;
  state: string;
  zip?: string;
  phone?: string;
  email?: string;
  logo?: string;
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

// API Response Types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
}