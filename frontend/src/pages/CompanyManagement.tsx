import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  Modal,
  message,
  Spin,
  Alert,
  Typography,
  Divider,
} from 'antd';
import {
  TeamOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import { Company, CompanyFormData, CompanyFilter } from '../types';
import { companyService } from '../services/companyService';
import CompanyTable from '../components/company/CompanyTable';
import CompanyForm from '../components/company/CompanyForm';

const { Title } = Typography;

const CompanyManagement: React.FC = () => {
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [formModalVisible, setFormModalVisible] = useState(false);
  const [filter, setFilter] = useState<CompanyFilter>({});
  
  const queryClient = useQueryClient();

  // Fetch companies with filters
  const {
    data: companies = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ['companies', filter],
    queryFn: () => companyService.getCompanies(filter.search, filter.city, filter.state),
  });

  // Create company mutation
  const createMutation = useMutation({
    mutationFn: companyService.createCompany,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      setFormModalVisible(false);
      setSelectedCompany(null);
    },
    onError: (error: any) => {
      message.error(error.message || '회사 등록에 실패했습니다.');
    },
  });

  // Update company mutation
  const updateMutation = useMutation({
    mutationFn: async (data: { id: string; company: Partial<Company> }) => {
      console.log('Updating company:', data);
      return companyService.updateCompany(data.id, data.company);
    },
    onSuccess: () => {
      message.success('회사 정보가 성공적으로 수정되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      setFormModalVisible(false);
      setSelectedCompany(null);
    },
    onError: (error: any) => {
      console.error('Update error:', error);
      const errorMessage = error.response?.data?.detail || error.message || '회사 정보 수정에 실패했습니다.';
      message.error(errorMessage);
    },
  });

  // Delete company mutation
  const deleteMutation = useMutation({
    mutationFn: companyService.deleteCompany,
    onSuccess: () => {
      message.success('회사가 성공적으로 삭제되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['companies'] });
    },
    onError: (error: any) => {
      console.error('Delete error:', error);
      message.error(error.message || '회사 삭제에 실패했습니다.');
    },
  });

  const handleAdd = () => {
    setSelectedCompany(null);
    setFormModalVisible(true);
  };

  const handleEdit = (company: Company) => {
    setSelectedCompany(company);
    setFormModalVisible(true);
  };

  const handleDelete = async (id: string) => {
    await deleteMutation.mutateAsync(id);
  };

  const handleSubmit = async (data: CompanyFormData) => {
    if (selectedCompany) {
      // Update existing company
      await updateMutation.mutateAsync({
        id: selectedCompany.id,
        company: data,
      });
    } else {
      // Create new company
      await createMutation.mutateAsync(data);
    }
  };

  const handleCancel = () => {
    setFormModalVisible(false);
    setSelectedCompany(null);
  };

  const isFormLoading = createMutation.isPending || updateMutation.isPending;

  if (error) {
    return (
      <Alert
        message="오류"
        description="회사 정보를 불러오는데 실패했습니다."
        type="error"
        showIcon
        style={{ margin: '24px 0' }}
      />
    );
  }

  return (
    <div>
      {/* Header */}
      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
          <TeamOutlined style={{ fontSize: 24, marginRight: 12, color: '#1890ff' }} />
          <Title level={2} style={{ margin: 0 }}>
            회사 정보 관리
          </Title>
        </div>
        <p style={{ margin: 0, color: '#666' }}>
          견적서 및 인보이스 발행에 사용할 회사 정보를 관리합니다.
        </p>
      </Card>

      <Divider />

      {/* Companies Table */}
      <Spin spinning={isLoading}>
        <CompanyTable
          companies={companies}
          loading={isLoading}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onAdd={handleAdd}
          filter={filter}
          onFilterChange={setFilter}
        />
      </Spin>

      {/* Company Form Modal */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center' }}>
            {selectedCompany ? (
              <>
                <TeamOutlined style={{ marginRight: 8 }} />
                회사 정보 수정
              </>
            ) : (
              <>
                <PlusOutlined style={{ marginRight: 8 }} />
                새 회사 등록
              </>
            )}
          </div>
        }
        open={formModalVisible}
        onCancel={handleCancel}
        footer={null}
        width={800}
        destroyOnHidden
        maskClosable={false}
      >
        <Divider style={{ margin: '16px 0 24px 0' }} />
        <CompanyForm
          initialData={selectedCompany || undefined}
          onSubmit={handleSubmit}
          onCancel={handleCancel}
          loading={isFormLoading}
        />
      </Modal>
    </div>
  );
};

export default CompanyManagement;