import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';
import koKR from 'antd/locale/ko_KR';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import Layout from './components/common/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AdminDashboard from './pages/AdminDashboard';
import DocumentList from './pages/DocumentList';
import CompanyManagement from './pages/CompanyManagement';
import InvoiceCreation from './pages/InvoiceCreation';
import PlumberReportCreation from './pages/PlumberReportCreation';
import WorkOrderCreation from './pages/WorkOrderCreation';
import WorkOrderList from './pages/WorkOrderList';
import WorkOrderDetail from './pages/WorkOrderDetail';
import DocumentTypesManagement from './pages/DocumentTypesManagement';
import TradesManagement from './pages/TradesManagement';
import DatabaseManagement from './pages/DatabaseManagement';
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
        <AuthProvider>
          <Router>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<Login />} />
              
              {/* Protected routes */}
              <Route path="/" element={
                <ProtectedRoute>
                  <Layout>
                    <Navigate to="/dashboard" replace />
                  </Layout>
                </ProtectedRoute>
              } />
              
              <Route path="/dashboard" element={
                <ProtectedRoute>
                  <Layout>
                    <Dashboard />
                  </Layout>
                </ProtectedRoute>
              } />
              
              {/* Admin only routes */}
              <Route path="/admin/dashboard" element={
                <ProtectedRoute requiredRole="admin">
                  <Layout>
                    <AdminDashboard />
                  </Layout>
                </ProtectedRoute>
              } />
              
              <Route path="/admin/document-types" element={
                <ProtectedRoute requiredRole="admin">
                  <Layout>
                    <DocumentTypesManagement />
                  </Layout>
                </ProtectedRoute>
              } />
              
              <Route path="/admin/trades" element={
                <ProtectedRoute requiredRole="admin">
                  <Layout>
                    <TradesManagement />
                  </Layout>
                </ProtectedRoute>
              } />
              
              <Route path="/admin/database" element={
                <ProtectedRoute requiredRole="admin">
                  <Layout>
                    <DatabaseManagement />
                  </Layout>
                </ProtectedRoute>
              } />
              
              {/* Manager and Admin routes */}
              <Route path="/companies" element={
                <ProtectedRoute requiredRole="manager">
                  <Layout>
                    <CompanyManagement />
                  </Layout>
                </ProtectedRoute>
              } />
              
              {/* Regular user routes */}
              <Route path="/documents" element={
                <ProtectedRoute>
                  <Layout>
                    <DocumentList />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/documents/:type" element={
                <ProtectedRoute>
                  <Layout>
                    <DocumentList />
                  </Layout>
                </ProtectedRoute>
              } />
              
              {/* Invoice Routes */}
              <Route path="/create/invoice" element={
                <ProtectedRoute>
                  <Layout>
                    <InvoiceCreation />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/invoices/:id" element={
                <ProtectedRoute>
                  <Layout>
                    <InvoiceCreation />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/invoices/:id/edit" element={
                <ProtectedRoute>
                  <Layout>
                    <InvoiceCreation />
                  </Layout>
                </ProtectedRoute>
              } />
              
              {/* Plumber Report Routes */}
              <Route path="/create/plumber" element={
                <ProtectedRoute>
                  <Layout>
                    <PlumberReportCreation />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/plumber-reports" element={
                <ProtectedRoute>
                  <Layout>
                    <PlumberReportCreation />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/plumber-reports/new" element={
                <ProtectedRoute>
                  <Layout>
                    <PlumberReportCreation />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/plumber-reports/:id" element={
                <ProtectedRoute>
                  <Layout>
                    <PlumberReportCreation />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/plumber-reports/:id/edit" element={
                <ProtectedRoute>
                  <Layout>
                    <PlumberReportCreation />
                  </Layout>
                </ProtectedRoute>
              } />
              
              {/* Work Order Routes */}
              <Route path="/work-orders" element={
                <ProtectedRoute>
                  <Layout>
                    <WorkOrderList />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/work-orders/new" element={
                <ProtectedRoute>
                  <Layout>
                    <WorkOrderCreation />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/work-orders/:id" element={
                <ProtectedRoute>
                  <Layout>
                    <WorkOrderDetail />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/work-orders/:id/edit" element={
                <ProtectedRoute>
                  <Layout>
                    <WorkOrderCreation />
                  </Layout>
                </ProtectedRoute>
              } />
              <Route path="/create/work-order" element={
                <ProtectedRoute>
                  <Layout>
                    <WorkOrderCreation />
                  </Layout>
                </ProtectedRoute>
              } />
            </Routes>
          </Router>
        </AuthProvider>
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export default App;
