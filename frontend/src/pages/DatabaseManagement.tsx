import React, { useState } from 'react';
import {
  Card,
  Tabs,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Typography,
  Alert,
  Tag,
} from 'antd';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  DatabaseOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import axios from 'axios';

const { Title } = Typography;
const { TabPane } = Tabs;

// Define table structures
interface TableConfig {
  name: string;
  displayName: string;
  endpoint: string;
  columns: ColumnsType<any>;
  formFields: FormField[];
}

interface FormField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'select' | 'textarea' | 'email';
  required?: boolean;
  options?: { value: any; label: string }[];
}

const DatabaseManagement: React.FC = () => {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('companies');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRecord, setEditingRecord] = useState<any>(null);
  const [form] = Form.useForm();

  // Table configurations
  const tables: Record<string, TableConfig> = {
    companies: {
      name: 'companies',
      displayName: 'Companies',
      endpoint: '/api/companies',
      columns: [
        { title: 'ID', dataIndex: 'id', key: 'id', width: 200 },
        { title: 'Company Name', dataIndex: 'name', key: 'name' },
        { title: 'Code', dataIndex: 'company_code', key: 'company_code' },
        { title: 'Phone', dataIndex: 'phone', key: 'phone' },
        { title: 'Email', dataIndex: 'email', key: 'email' },
        { title: 'City', dataIndex: 'city', key: 'city' },
        {
          title: 'Actions',
          key: 'actions',
          width: 120,
          render: (_, record) => (
            <Space>
              <Button
                type="link"
                icon={<EditOutlined />}
                onClick={() => handleEdit(record)}
              />
              <Popconfirm
                title="Are you sure you want to delete?"
                onConfirm={() => handleDelete(record.id)}
              >
                <Button type="link" danger icon={<DeleteOutlined />} />
              </Popconfirm>
            </Space>
          ),
        },
      ],
      formFields: [
        { name: 'name', label: 'Company Name', type: 'text', required: true },
        { name: 'company_code', label: 'Company Code', type: 'text' },
        { name: 'address', label: 'Address', type: 'text' },
        { name: 'city', label: 'City', type: 'text' },
        { name: 'state', label: 'State', type: 'text' },
        { name: 'zipcode', label: 'ZIP Code', type: 'text' },
        { name: 'phone', label: 'Phone', type: 'text' },
        { name: 'email', label: 'Email', type: 'email' },
        { name: 'website', label: 'Website', type: 'text' },
        { name: 'license_number', label: 'License Number', type: 'text' },
      ],
    },
    invoices: {
      name: 'invoices',
      displayName: 'Invoices',
      endpoint: '/api/invoices',
      columns: [
        { title: 'ID', dataIndex: 'id', key: 'id', width: 200 },
        { title: 'Invoice Number', dataIndex: 'invoice_number', key: 'invoice_number' },
        { title: 'Client Name', dataIndex: 'client_name', key: 'client_name' },
        {
          title: 'Total Amount',
          dataIndex: 'total_amount',
          key: 'total_amount',
          render: (amount: number) => `$${amount?.toFixed(2) || '0.00'}`,
        },
        {
          title: 'Status',
          dataIndex: 'status',
          key: 'status',
          render: (status: string) => {
            const colors: Record<string, string> = {
              pending: 'orange',
              paid: 'green',
              overdue: 'red',
              cancelled: 'default',
            };
            return <Tag color={colors[status] || 'default'}>{status}</Tag>;
          },
        },
        { title: 'Date', dataIndex: 'invoice_date', key: 'invoice_date' },
        {
          title: 'Actions',
          key: 'actions',
          width: 120,
          render: (_, record) => (
            <Space>
              <Button
                type="link"
                icon={<EditOutlined />}
                onClick={() => handleEdit(record)}
              />
              <Popconfirm
                title="Are you sure you want to delete?"
                onConfirm={() => handleDelete(record.id)}
              >
                <Button type="link" danger icon={<DeleteOutlined />} />
              </Popconfirm>
            </Space>
          ),
        },
      ],
      formFields: [
        { name: 'invoice_number', label: '송장 번호', type: 'text', required: true },
        { name: 'client_name', label: '고객명', type: 'text', required: true },
        { name: 'client_address', label: '고객 주소', type: 'text' },
        { name: 'client_phone', label: '고객 전화번호', type: 'text' },
        { name: 'client_email', label: '고객 이메일', type: 'email' },
        {
          name: 'status',
          label: 'Status',
          type: 'select',
          options: [
            { value: 'pending', label: 'Pending' },
            { value: 'paid', label: 'Paid' },
            { value: 'overdue', label: 'Overdue' },
            { value: 'cancelled', label: 'Cancelled' },
          ],
        },
        { name: 'total_amount', label: 'Total Amount', type: 'number' },
        { name: 'notes', label: 'Notes', type: 'textarea' },
      ],
    },
    estimates: {
      name: 'estimates',
      displayName: 'Estimates',
      endpoint: '/api/estimates',
      columns: [
        { title: 'ID', dataIndex: 'id', key: 'id', width: 200 },
        { title: 'Estimate Number', dataIndex: 'estimate_number', key: 'estimate_number' },
        { title: '고객명', dataIndex: 'client_name', key: 'client_name' },
        {
          title: '총액',
          dataIndex: 'total_amount',
          key: 'total_amount',
          render: (amount: number) => `$${amount?.toFixed(2) || '0.00'}`,
        },
        {
          title: '상태',
          dataIndex: 'status',
          key: 'status',
          render: (status: string) => {
            const colors: Record<string, string> = {
              draft: 'default',
              sent: 'blue',
              accepted: 'green',
              rejected: 'red',
              expired: 'orange',
            };
            return <Tag color={colors[status] || 'default'}>{status}</Tag>;
          },
        },
        { title: '날짜', dataIndex: 'estimate_date', key: 'estimate_date' },
        {
          title: 'Actions',
          key: 'actions',
          width: 120,
          render: (_, record) => (
            <Space>
              <Button
                type="link"
                icon={<EditOutlined />}
                onClick={() => handleEdit(record)}
              />
              <Popconfirm
                title="Are you sure you want to delete?"
                onConfirm={() => handleDelete(record.id)}
              >
                <Button type="link" danger icon={<DeleteOutlined />} />
              </Popconfirm>
            </Space>
          ),
        },
      ],
      formFields: [
        { name: 'estimate_number', label: 'Estimate Number', type: 'text', required: true },
        { name: 'client_name', label: 'Client Name', type: 'text', required: true },
        { name: 'client_address', label: 'Client Address', type: 'text' },
        { name: 'client_phone', label: 'Client Phone', type: 'text' },
        { name: 'client_email', label: 'Client Email', type: 'email' },
        {
          name: 'status',
          label: 'Status',
          type: 'select',
          options: [
            { value: 'draft', label: 'Draft' },
            { value: 'sent', label: 'Sent' },
            { value: 'accepted', label: 'Accepted' },
            { value: 'rejected', label: 'Rejected' },
            { value: 'expired', label: 'Expired' },
          ],
        },
        { name: 'total_amount', label: 'Total Amount', type: 'number' },
        { name: 'notes', label: 'Notes', type: 'textarea' },
      ],
    },
  };

  const currentTable = tables[activeTab];

  // Fetch data
  const { data, isLoading, refetch, error } = useQuery({
    queryKey: ['database', activeTab],
    queryFn: async () => {
      try {
        const response = await axios.get(currentTable.endpoint);
        // Convert API response to array format if needed
        const responseData = response.data;
        if (Array.isArray(responseData)) {
          return responseData;
        } else if (responseData?.items && Array.isArray(responseData.items)) {
          return responseData.items;
        } else if (responseData?.data && Array.isArray(responseData.data)) {
          return responseData.data;
        }
        console.warn('API response format is different than expected:', responseData);
        return [];
      } catch (error) {
        console.error('Failed to load data:', error);
        message.error('Failed to load data.');
        return [];
      }
    },
  });

  // Create/Update mutation
  const saveMutation = useMutation({
    mutationFn: async (values: any) => {
      if (editingRecord) {
        return axios.put(`${currentTable.endpoint}/${editingRecord.id}`, values);
      }
      return axios.post(currentTable.endpoint, values);
    },
    onSuccess: () => {
      message.success(`${currentTable.displayName} ${editingRecord ? 'updated' : 'created'} successfully`);
      queryClient.invalidateQueries({ queryKey: ['database', activeTab] });
      handleCloseModal();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Operation failed');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      return axios.delete(`${currentTable.endpoint}/${id}`);
    },
    onSuccess: () => {
      message.success(`${currentTable.displayName} deleted successfully`);
      queryClient.invalidateQueries({ queryKey: ['database', activeTab] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Delete failed');
    },
  });

  const handleAdd = () => {
    setEditingRecord(null);
    form.resetFields();
    setIsModalOpen(true);
  };

  const handleEdit = (record: any) => {
    setEditingRecord(record);
    form.setFieldsValue(record);
    setIsModalOpen(true);
  };

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingRecord(null);
    form.resetFields();
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      saveMutation.mutate(values);
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <Space>
            <DatabaseOutlined />
            <span>Database Management</span>
          </Space>
        }
      >
        <Alert
          message="Direct Database Management"
          description="This page allows you to directly view, create, update, and delete database records. Please work carefully."
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {Object.entries(tables).map(([key, config]) => (
            <TabPane tab={config.displayName} key={key}>
              <Space style={{ marginBottom: 16 }}>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleAdd}
                >
                  Add New {config.displayName}
                </Button>
                <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
                  Refresh
                </Button>
              </Space>

              <Table
                columns={config.columns}
                dataSource={data || []}
                rowKey="id"
                loading={isLoading}
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showTotal: (total) => `Total ${total} items`,
                }}
              />
            </TabPane>
          ))}
        </Tabs>

        <Modal
          title={`${editingRecord ? 'Edit' : 'Add'} ${currentTable.displayName}`}
          open={isModalOpen}
          onOk={handleSubmit}
          onCancel={handleCloseModal}
          width={600}
          confirmLoading={saveMutation.isPending}
        >
          <Form form={form} layout="vertical">
            {currentTable.formFields.map((field) => (
              <Form.Item
                key={field.name}
                name={field.name}
                label={field.label}
                rules={[
                  {
                    required: field.required,
                    message: `Please enter ${field.label}`,
                  },
                ]}
              >
                {field.type === 'textarea' ? (
                  <Input.TextArea rows={3} />
                ) : field.type === 'select' ? (
                  <Select>
                    {field.options?.map((option) => (
                      <Select.Option key={option.value} value={option.value}>
                        {option.label}
                      </Select.Option>
                    ))}
                  </Select>
                ) : field.type === 'number' ? (
                  <Input type="number" step="0.01" />
                ) : (
                  <Input type={field.type} />
                )}
              </Form.Item>
            ))}
          </Form>
        </Modal>
      </Card>
    </div>
  );
};

export default DatabaseManagement;