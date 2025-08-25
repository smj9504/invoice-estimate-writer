import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import koKR from 'antd/locale/ko_KR';
import Layout from './components/common/Layout';
import Dashboard from './pages/Dashboard';
import DocumentList from './pages/DocumentList';
import CompanyManagement from './pages/CompanyManagement';
import InvoiceCreation from './pages/InvoiceCreation';
import PlumberReportCreation from './pages/PlumberReportCreation';
import WorkOrderCreation from './pages/WorkOrderCreation';
import WorkOrderList from './pages/WorkOrderList';
import 'antd/dist/reset.css';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider locale={koKR}>
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/companies" element={<CompanyManagement />} />
              <Route path="/documents" element={<DocumentList />} />
              <Route path="/documents/:type" element={<DocumentList />} />
              
              {/* Invoice Routes */}
              <Route path="/create/invoice" element={<InvoiceCreation />} />
              <Route path="/invoices/:id" element={<InvoiceCreation />} />
              <Route path="/invoices/:id/edit" element={<InvoiceCreation />} />
              
              {/* Plumber Report Routes */}
              <Route path="/create/plumber" element={<PlumberReportCreation />} />
              <Route path="/plumber-reports" element={<PlumberReportCreation />} />
              <Route path="/plumber-reports/new" element={<PlumberReportCreation />} />
              <Route path="/plumber-reports/:id" element={<PlumberReportCreation />} />
              <Route path="/plumber-reports/:id/edit" element={<PlumberReportCreation />} />
              
              {/* Work Order Routes */}
              <Route path="/work-orders" element={<WorkOrderList />} />
              <Route path="/work-orders/new" element={<WorkOrderCreation />} />
              <Route path="/work-orders/:id" element={<WorkOrderCreation />} />
              <Route path="/work-orders/:id/edit" element={<WorkOrderCreation />} />
              <Route path="/create/work-order" element={<WorkOrderCreation />} />
            </Routes>
          </Layout>
        </Router>
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export default App;
