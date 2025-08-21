import React, { useState, useEffect } from 'react';
import {
  Table,
  Card,
  Button,
  Space,
  Tag,
  Input,
  Select,
  Row,
  Col,
  message,
  Popconfirm,
  Tooltip,
  Typography,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  FilePdfOutlined,
  CopyOutlined,
  SearchOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import { invoiceService } from '../services/invoiceService';

const { Title } = Typography;
const { Option } = Select;

interface Invoice {
  id: number;
  invoice_number: string;
  date: string;
  due_date: string;
  company_name: string;
  client_name: string;
  total: number;
  paid_amount: number;
  status: string;
  created_at: string;
  updated_at: string;
}

const InvoiceList: React.FC = () => {
  const navigate = useNavigate();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);

  useEffect(() => {
    loadInvoices();
  }, []);

  const loadInvoices = async () => {
    try {
      setLoading(true);
      const data = await invoiceService.getInvoices();
      setInvoices(data);
    } catch (error) {
      console.error('Failed to load invoices:', error);
      message.error('Failed to load invoices');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await invoiceService.deleteInvoice(id);
      message.success('Invoice deleted successfully');
      loadInvoices();
    } catch (error) {
      console.error('Failed to delete invoice:', error);
      message.error('Failed to delete invoice');
    }
  };

  const handleDuplicate = async (id: number) => {
    try {
      const response = await invoiceService.duplicateInvoice(id);
      message.success('Invoice duplicated successfully');
      navigate(`/invoices/${response.id}/edit`);
    } catch (error) {
      console.error('Failed to duplicate invoice:', error);
      message.error('Failed to duplicate invoice');
    }
  };

  const handleDownloadPDF = async (id: number) => {
    try {
      const blob = await invoiceService.generatePDF(id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `invoice_${id}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
      message.success('PDF downloaded successfully');
    } catch (error) {
      console.error('Failed to download PDF:', error);
      message.error('Failed to download PDF');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'paid':
        return 'green';
      case 'sent':
        return 'blue';
      case 'overdue':
        return 'red';
      case 'cancelled':
        return 'gray';
      case 'draft':
      default:
        return 'default';
    }
  };

  const getStatusText = (status: string) => {
    return status.charAt(0).toUpperCase() + status.slice(1);
  };

  const filteredInvoices = invoices.filter(invoice => {
    const matchesSearch = !searchText || 
      invoice.invoice_number.toLowerCase().includes(searchText.toLowerCase()) ||
      invoice.client_name.toLowerCase().includes(searchText.toLowerCase()) ||
      invoice.company_name.toLowerCase().includes(searchText.toLowerCase());
    
    const matchesStatus = !statusFilter || invoice.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  const columns = [
    {
      title: 'Invoice #',
      dataIndex: 'invoice_number',
      key: 'invoice_number',
      sorter: (a: Invoice, b: Invoice) => a.invoice_number.localeCompare(b.invoice_number),
      render: (text: string) => <strong>{text}</strong>,
    },
    {
      title: 'Date',
      dataIndex: 'date',
      key: 'date',
      sorter: (a: Invoice, b: Invoice) => dayjs(a.date).unix() - dayjs(b.date).unix(),
      render: (date: string) => dayjs(date).format('MMM DD, YYYY'),
    },
    {
      title: 'Due Date',
      dataIndex: 'due_date',
      key: 'due_date',
      sorter: (a: Invoice, b: Invoice) => dayjs(a.due_date).unix() - dayjs(b.due_date).unix(),
      render: (date: string, record: Invoice) => {
        const dueDate = dayjs(date);
        const isOverdue = dueDate.isBefore(dayjs()) && record.status !== 'paid';
        return (
          <span style={{ color: isOverdue ? '#ff4d4f' : undefined }}>
            {dueDate.format('MMM DD, YYYY')}
          </span>
        );
      },
    },
    {
      title: 'Company',
      dataIndex: 'company_name',
      key: 'company_name',
      sorter: (a: Invoice, b: Invoice) => a.company_name.localeCompare(b.company_name),
      ellipsis: true,
    },
    {
      title: 'Client',
      dataIndex: 'client_name',
      key: 'client_name',
      sorter: (a: Invoice, b: Invoice) => a.client_name.localeCompare(b.client_name),
      ellipsis: true,
    },
    {
      title: 'Total',
      dataIndex: 'total',
      key: 'total',
      sorter: (a: Invoice, b: Invoice) => a.total - b.total,
      render: (amount: number) => `$${amount.toFixed(2)}`,
      align: 'right' as const,
    },
    {
      title: 'Balance',
      key: 'balance',
      render: (_: any, record: Invoice) => {
        const balance = record.total - (record.paid_amount || 0);
        return (
          <span style={{ color: balance > 0 ? '#ff4d4f' : '#52c41a' }}>
            ${balance.toFixed(2)}
          </span>
        );
      },
      align: 'right' as const,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      filters: [
        { text: 'Draft', value: 'draft' },
        { text: 'Sent', value: 'sent' },
        { text: 'Paid', value: 'paid' },
        { text: 'Overdue', value: 'overdue' },
        { text: 'Cancelled', value: 'cancelled' },
      ],
      onFilter: (value: any, record: Invoice) => record.status === value,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {getStatusText(status)}
        </Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 200,
      render: (_: any, record: Invoice) => (
        <Space size="small">
          <Tooltip title="View">
            <Button
              size="small"
              icon={<EyeOutlined />}
              onClick={() => navigate(`/invoices/${record.id}`)}
            />
          </Tooltip>
          <Tooltip title="Edit">
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => navigate(`/invoices/${record.id}/edit`)}
            />
          </Tooltip>
          <Tooltip title="Download PDF">
            <Button
              size="small"
              icon={<FilePdfOutlined />}
              onClick={() => handleDownloadPDF(record.id)}
            />
          </Tooltip>
          <Tooltip title="Duplicate">
            <Button
              size="small"
              icon={<CopyOutlined />}
              onClick={() => handleDuplicate(record.id)}
            />
          </Tooltip>
          <Popconfirm
            title="Delete this invoice?"
            description="This action cannot be undone."
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Tooltip title="Delete">
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2}>Invoices</Title>
        </Col>
        <Col>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            size="large"
            onClick={() => navigate('/invoices/create')}
          >
            Create Invoice
          </Button>
        </Col>
      </Row>

      <Card>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col xs={24} sm={12} md={8}>
            <Input
              placeholder="Search by invoice #, client, or company"
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              allowClear
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="Filter by status"
              style={{ width: '100%' }}
              value={statusFilter}
              onChange={setStatusFilter}
              allowClear
            >
              <Option value="draft">Draft</Option>
              <Option value="sent">Sent</Option>
              <Option value="paid">Paid</Option>
              <Option value="overdue">Overdue</Option>
              <Option value="cancelled">Cancelled</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={2}>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadInvoices}
              loading={loading}
              block
            >
              Refresh
            </Button>
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={filteredInvoices}
          rowKey={(record) => record.id}
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} invoices`,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>
    </div>
  );
};

export default InvoiceList;