import { create } from 'zustand';
import { Company, Document, DocumentFilter } from '../types';

interface AppState {
  // Company state
  companies: Company[];
  selectedCompany: Company | null;
  setCompanies: (companies: Company[]) => void;
  setSelectedCompany: (company: Company | null) => void;
  
  // Document state
  documents: Document[];
  documentFilter: DocumentFilter;
  setDocuments: (documents: Document[]) => void;
  setDocumentFilter: (filter: DocumentFilter) => void;
  
  // UI state
  loading: boolean;
  error: string | null;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // Current document being edited
  currentDocument: Document | null;
  setCurrentDocument: (document: Document | null) => void;
}

export const useStore = create<AppState>((set) => ({
  // Company state
  companies: [],
  selectedCompany: null,
  setCompanies: (companies) => set({ companies }),
  setSelectedCompany: (company) => set({ selectedCompany: company }),
  
  // Document state
  documents: [],
  documentFilter: {},
  setDocuments: (documents) => set({ documents }),
  setDocumentFilter: (filter) => set({ documentFilter: filter }),
  
  // UI state
  loading: false,
  error: null,
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  
  // Current document
  currentDocument: null,
  setCurrentDocument: (document) => set({ currentDocument: document }),
}));