import React, { useState, useEffect, useCallback } from 'react';
import {
  Form,
  Input,
  Button,
  Select,
  Card,
  Row,
  Col,
  Space,
  message,
  Typography,
  Divider,
  Spin
} from 'antd';
import {
  SaveOutlined,
  SendOutlined,
  EyeOutlined,
  FileTextOutlined,
  UserOutlined,
  ToolOutlined,
  DollarOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';

import { companyService } from '../services/companyService';
import { workOrderService } from '../services/workOrderService';
import CompanySelector from '../components/work-order/CompanySelector';
import CostCalculationPanel from '../components/work-order/CostCalculationPanel';
import RichTextEditor from '../components/editor/RichTextEditor';
import { useStore } from '../store/useStore';
import { Company, WorkOrderFormData, Credit } from '../types';

const { Title } = Typography;
const { TextArea } = Input;
const { Option } = Select;

const WorkOrderCreation: React.FC = () => {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const [finalCost, setFinalCost] = useState(0);
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [availableCredits, setAvailableCredits] = useState<Credit[]>([]);
  const [workDescription, setWorkDescription] = useState('');
  
  const {
    companies,
    setCompanies,
    loading,
    setLoading,
    setError
  } = useStore();

  // Load companies
  const { data: companiesData, isLoading: companiesLoading, error: companiesError } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companyService.getCompanies(),
  });

  // Handle companies data
  useEffect(() => {
    if (companiesData) {
      setCompanies(companiesData);
    }
  }, [companiesData]);

  // Handle companies error
  useEffect(() => {
    if (companiesError) {
      console.error('Failed to load companies:', companiesError);
      message.error('Failed to load companies');
    }
  }, [companiesError]);

  // Load available trades (using mock data for now)
  const { data: trades = [] } = useQuery({
    queryKey: ['trades'],
    queryFn: () => Promise.resolve(workOrderService.getMockTrades()),
  });

  // Load document types (using mock data for now)
  const { data: documentTypes = [] } = useQuery({
    queryKey: ['documentTypes'],
    queryFn: () => Promise.resolve(workOrderService.getMockDocumentTypes()),
  });

  // Create work order mutation
  const createWorkOrderMutation = useMutation({
    mutationFn: (data: WorkOrderFormData) => workOrderService.createWorkOrder(data),
    onSuccess: (response) => {
      message.success('Work order created successfully!');
      navigate(`/work-orders/${response.id}`);
    },
    onError: (error: any) => {
      console.error('Failed to create work order:', error);
      message.error(error.response?.data?.message || 'Failed to create work order');
    }
  });

  // Load credits when company is selected
  useEffect(() => {
    if (selectedCompany?.id) {
      // Mock credits for now
      const mockCredits: Credit[] = [
        {
          id: '1',
          company_id: selectedCompany.id,
          amount: 100,
          description: 'Loyalty Credit',
          is_active: true,
          created_at: '2024-01-01'
        },
        {
          id: '2',
          company_id: selectedCompany.id,
          amount: 50,
          description: 'Referral Bonus',
          is_active: true,
          created_at: '2024-01-15'
        }
      ];
      setAvailableCredits(mockCredits);
    } else {
      setAvailableCredits([]);
    }
  }, [selectedCompany]);

  const handleCompanySelect = (companyId: string) => {
    const company = companies.find(c => c.id === companyId);
    setSelectedCompany(company || null);
  };

  const handleSave = async (status: 'draft' | 'pending' = 'draft') => {
    try {
      const values = await form.validateFields();
      
      if (!selectedCompany) {
        message.error('Please select a company');
        return;
      }

      const workOrderData: WorkOrderFormData = {
        company_id: selectedCompany.id,
        document_type: values.document_type,
        client_name: values.client_name,
        client_phone: values.client_phone,
        client_email: values.client_email,
        client_address: values.client_address,
        client_city: values.client_city,
        client_state: values.client_state,
        client_zipcode: values.client_zipcode,
        trades: values.trades || [],
        work_description: workDescription,
        consultation_notes: values.consultation_notes,
        cost_override: values.cost_override
      };

      createWorkOrderMutation.mutate(workOrderData);
    } catch (error) {
      console.error('Validation failed:', error);
      message.error('Please fill in all required fields');
    }
  };

  const handlePreview = () => {
    // TODO: Implement PDF preview
    message.info('PDF preview functionality will be implemented');
  };

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>
        <FileTextOutlined style={{ marginRight: 8 }} />
        Create Work Order
      </Title>

      <Form
        form={form}
        layout="vertical"
        onFinish={() => handleSave('pending')}
      >
        <Row gutter={24}>
          {/* Company Selection */}
          <Col xs={24}>
            <Card
              title={
                <Space>
                  <UserOutlined />
                  <span>Company Information</span>
                </Space>
              }
              style={{ marginBottom: 24 }}
            >
              <CompanySelector
                companies={companies}
                selectedCompany={selectedCompany}
                onCompanySelect={handleCompanySelect}
                loading={companiesLoading}
                showCompanyInfo={true}
              />
            </Card>
          </Col>

          {/* Document Type and Basic Info */}
          <Col xs={24} lg={12}>
            <Card
              title={
                <Space>
                  <FileTextOutlined />
                  <span>Work Order Details</span>
                </Space>
              }
              style={{ marginBottom: 24 }}
            >
              <Form.Item
                name="document_type"
                label="Document Type"
                rules={[{ required: true, message: 'Please select a document type' }]}
              >
                <Select placeholder="Select document type" size="large">
                  {documentTypes.map(type => (
                    <Option key={type.id} value={type.id}>
                      {type.name} {type.base_cost > 0 && `(Base: $${type.base_cost})`}
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="trades"
                label="Trades Required"
                rules={[{ required: true, message: 'Please select at least one trade' }]}
              >
                <Select
                  mode="multiple"
                  placeholder="Select trades..."
                  size="large"
                  showSearch
                  filterOption={(input, option) =>
                    option?.children?.toString().toLowerCase().includes(input.toLowerCase()) || false
                  }
                >
                  {trades.map(trade => (
                    <Option key={trade.id} value={trade.name.toLowerCase()}>
                      <Space>
                        <ToolOutlined />
                        {trade.name}
                        <span style={{ color: '#666', fontSize: '12px' }}>
                          (+${trade.base_cost})
                        </span>
                      </Space>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Card>
          </Col>

          {/* Cost Calculation */}
          <Col xs={24} lg={12}>
            <CostCalculationPanel
              documentType={form.getFieldValue('document_type')}
              selectedTrades={form.getFieldValue('trades') || []}
              availableCredits={availableCredits}
              companyId={selectedCompany?.id || ''}
              onCostChange={setFinalCost}
            />
          </Col>

          {/* Client Information */}
          <Col xs={24}>
            <Card
              title={
                <Space>
                  <UserOutlined />
                  <span>Client Information</span>
                </Space>
              }
              style={{ marginBottom: 24 }}
            >
              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="client_name"
                    label="Client Name"
                    rules={[{ required: true, message: 'Please enter client name' }]}
                  >
                    <Input placeholder="Enter client name" size="large" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item name="client_phone" label="Phone">
                    <Input placeholder="Enter phone number" size="large" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item name="client_email" label="Email">
                    <Input type="email" placeholder="Enter email address" size="large" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item name="client_address" label="Address">
                    <Input placeholder="Enter address" size="large" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={8}>
                  <Form.Item name="client_city" label="City">
                    <Input placeholder="City" size="large" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={8}>
                  <Form.Item name="client_state" label="State">
                    <Input placeholder="State" size="large" />
                  </Form.Item>
                </Col>
                <Col xs={24} md={8}>
                  <Form.Item name="client_zipcode" label="ZIP Code">
                    <Input placeholder="ZIP" size="large" />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
          </Col>

          {/* Work Description */}
          <Col xs={24}>
            <Card
              title={
                <Space>
                  <ToolOutlined />
                  <span>Work Description</span>
                </Space>
              }
              style={{ marginBottom: 24 }}
            >
              <Form.Item label="Detailed Work Description">
                <div style={{ border: '1px solid #d9d9d9', borderRadius: '6px' }}>
                  <RichTextEditor
                    value={workDescription}
                    onChange={setWorkDescription}
                    placeholder="Describe the work to be performed in detail..."
                    minHeight={200}
                  />
                </div>
              </Form.Item>

              <Form.Item name="consultation_notes" label="Phone Consultation Notes">
                <TextArea
                  rows={4}
                  placeholder="Notes from phone consultation with client..."
                />
              </Form.Item>
            </Card>
          </Col>
        </Row>

        {/* Action Buttons */}
        <Card>
          <Row justify="space-between" align="middle">
            <Col>
              <Space size="middle">
                <Button
                  size="large"
                  onClick={() => navigate('/work-orders')}
                >
                  Cancel
                </Button>
                <Button
                  type="default"
                  size="large"
                  icon={<SaveOutlined />}
                  onClick={() => handleSave('draft')}
                  loading={createWorkOrderMutation.isPending}
                >
                  Save as Draft
                </Button>
              </Space>
            </Col>
            <Col>
              <Space size="middle">
                <Button
                  size="large"
                  icon={<EyeOutlined />}
                  onClick={handlePreview}
                  disabled={!selectedCompany}
                >
                  Preview PDF
                </Button>
                <Button
                  type="primary"
                  size="large"
                  icon={<SendOutlined />}
                  htmlType="submit"
                  loading={createWorkOrderMutation.isPending}
                  disabled={!selectedCompany}
                >
                  Create & Send Work Order
                </Button>
              </Space>
            </Col>
          </Row>

          {/* Cost Summary */}
          {finalCost > 0 && (
            <>
              <Divider />
              <Row justify="center">
                <Col>
                  <Space align="center" size="large">
                    <DollarOutlined style={{ fontSize: '20px', color: '#1890ff' }} />
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '12px', color: '#666' }}>Estimated Cost</div>
                      <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
                        ${finalCost.toFixed(2)}
                      </div>
                    </div>
                  </Space>
                </Col>
              </Row>
            </>
          )}
        </Card>
      </Form>
    </div>
  );
};

export default WorkOrderCreation;