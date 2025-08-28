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
      displayName: '회사',
      endpoint: '/api/companies',
      columns: [
        { title: 'ID', dataIndex: 'id', key: 'id', width: 200 },
        { title: '회사명', dataIndex: 'name', key: 'name' },
        { title: '코드', dataIndex: 'company_code', key: 'company_code' },
        { title: '전화번호', dataIndex: 'phone', key: 'phone' },
        { title: '이메일', dataIndex: 'email', key: 'email' },
        { title: '도시', dataIndex: 'city', key: 'city' },
        {
          title: '작업',
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
                title="삭제하시겠습니까?"
                onConfirm={() => handleDelete(record.id)}
              >
                <Button type="link" danger icon={<DeleteOutlined />} />
              </Popconfirm>
            </Space>
          ),
        },
      ],
      formFields: [
        { name: 'name', label: '회사명', type: 'text', required: true },
        { name: 'company_code', label: '회사 코드', type: 'text' },
        { name: 'address', label: '주소', type: 'text' },
        { name: 'city', label: '도시', type: 'text' },
        { name: 'state', label: '주/도', type: 'text' },
        { name: 'zipcode', label: '우편번호', type: 'text' },
        { name: 'phone', label: '전화번호', type: 'text' },
        { name: 'email', label: '이메일', type: 'email' },
        { name: 'website', label: '웹사이트', type: 'text' },
        { name: 'license_number', label: '사업자 번호', type: 'text' },
      ],
    },
    invoices: {
      name: 'invoices',
      displayName: '송장',
      endpoint: '/api/invoices',
      columns: [
        { title: 'ID', dataIndex: 'id', key: 'id', width: 200 },
        { title: '송장 번호', dataIndex: 'invoice_number', key: 'invoice_number' },
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
              pending: 'orange',
              paid: 'green',
              overdue: 'red',
              cancelled: 'default',
            };
            return <Tag color={colors[status] || 'default'}>{status}</Tag>;
          },
        },
        { title: '날짜', dataIndex: 'invoice_date', key: 'invoice_date' },
        {
          title: '작업',
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
                title="삭제하시겠습니까?"
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
          label: '상태',
          type: 'select',
          options: [
            { value: 'pending', label: '대기중' },
            { value: 'paid', label: '지불완료' },
            { value: 'overdue', label: '연체' },
            { value: 'cancelled', label: '취소됨' },
          ],
        },
        { name: 'total_amount', label: '총액', type: 'number' },
        { name: 'notes', label: '메모', type: 'textarea' },
      ],
    },
    estimates: {
      name: 'estimates',
      displayName: '견적서',
      endpoint: '/api/estimates',
      columns: [
        { title: 'ID', dataIndex: 'id', key: 'id', width: 200 },
        { title: '견적 번호', dataIndex: 'estimate_number', key: 'estimate_number' },
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
          title: '작업',
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
                title="삭제하시겠습니까?"
                onConfirm={() => handleDelete(record.id)}
              >
                <Button type="link" danger icon={<DeleteOutlined />} />
              </Popconfirm>
            </Space>
          ),
        },
      ],
      formFields: [
        { name: 'estimate_number', label: '견적 번호', type: 'text', required: true },
        { name: 'client_name', label: '고객명', type: 'text', required: true },
        { name: 'client_address', label: '고객 주소', type: 'text' },
        { name: 'client_phone', label: '고객 전화번호', type: 'text' },
        { name: 'client_email', label: '고객 이메일', type: 'email' },
        {
          name: 'status',
          label: '상태',
          type: 'select',
          options: [
            { value: 'draft', label: '초안' },
            { value: 'sent', label: '발송됨' },
            { value: 'accepted', label: '승인됨' },
            { value: 'rejected', label: '거절됨' },
            { value: 'expired', label: '만료됨' },
          ],
        },
        { name: 'total_amount', label: '총액', type: 'number' },
        { name: 'notes', label: '메모', type: 'textarea' },
      ],
    },
  };

  const currentTable = tables[activeTab];

  // Fetch data
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['database', activeTab],
    queryFn: async () => {
      const response = await axios.get(currentTable.endpoint);
      return response.data;
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
      message.success(`${currentTable.displayName} ${editingRecord ? '수정' : '생성'}됨`);
      queryClient.invalidateQueries({ queryKey: ['database', activeTab] });
      handleCloseModal();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '작업 실패');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      return axios.delete(`${currentTable.endpoint}/${id}`);
    },
    onSuccess: () => {
      message.success(`${currentTable.displayName} 삭제됨`);
      queryClient.invalidateQueries({ queryKey: ['database', activeTab] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '삭제 실패');
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
            <span>데이터베이스 관리</span>
          </Space>
        }
      >
        <Alert
          message="데이터베이스 직접 관리"
          description="이 페이지에서는 데이터베이스 테이블을 직접 조회, 생성, 수정, 삭제할 수 있습니다. 주의하여 작업하세요."
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
                  새 {config.displayName} 추가
                </Button>
                <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
                  새로고침
                </Button>
              </Space>

              <Table
                columns={config.columns}
                dataSource={data}
                rowKey="id"
                loading={isLoading}
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showTotal: (total) => `총 ${total}개`,
                }}
              />
            </TabPane>
          ))}
        </Tabs>

        <Modal
          title={`${editingRecord ? '수정' : '추가'} ${currentTable.displayName}`}
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
                    message: `${field.label}을(를) 입력하세요`,
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