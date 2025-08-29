import React, { useState } from 'react';
import { 
  Table, 
  Card, 
  Button, 
  Space, 
  Tag, 
  Input, 
  Select, 
  DatePicker, 
  Row, 
  Col,
  Dropdown,
  Modal,
  message,
  Typography,
} from 'antd';
import {
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  DownloadOutlined,
  MailOutlined,
  CopyOutlined,
  MoreOutlined,
  SearchOutlined,
  FilterOutlined,
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentService } from '../services/documentService';
import { Document, DocumentFilter, DocumentType } from '../types';
import dayjs from 'dayjs';

const { Title } = Typography;
const { RangePicker } = DatePicker;

const DocumentList: React.FC = () => {
  const navigate = useNavigate();
  const { type } = useParams<{ type: string }>();
  const queryClient = useQueryClient();
  
  const [filter, setFilter] = useState<DocumentFilter>({
    type: type as DocumentType,
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  // Fetch documents
  const { data, isLoading } = useQuery({
    queryKey: ['documents', filter, currentPage, pageSize],
    queryFn: () => documentService.getDocuments(filter, currentPage, pageSize),
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: documentService.deleteDocument,
    onSuccess: () => {
      message.success('Document has been deleted');
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: () => {
      message.error('An error occurred during deletion');
    },
  });

  // Duplicate mutation
  const duplicateMutation = useMutation({
    mutationFn: documentService.duplicateDocument,
    onSuccess: () => {
      message.success('Document has been duplicated');
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: () => {
      message.error('An error occurred during duplication');
    },
  });

  const handleDelete = (id: string) => {
    Modal.confirm({
      title: 'Delete Document',
      content: 'Are you sure you want to delete this document?',
      okText: 'Delete',
      cancelText: 'Cancel',
      okType: 'danger',
      onOk: () => deleteMutation.mutate(id),
    });
  };

  const handleDownloadPDF = async (id: string) => {
    try {
      const blob = await documentService.generatePDF(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `document_${id}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      message.error('An error occurred during PDF download');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'default';
      case 'sent': return 'processing';
      case 'paid': return 'success';
      case 'cancelled': return 'error';
      default: return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'draft': return 'Draft';
      case 'sent': return 'Sent';
      case 'paid': return 'Paid';
      case 'cancelled': return 'Cancelled';
      default: return status;
    }
  };

  const columns = [
    {
      title: 'Document Number',
      dataIndex: 'document_number',
      key: 'document_number',
      width: 150,
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (type: DocumentType) => {
        const typeMap = {
          estimate: 'Estimate',
          invoice: 'Invoice',
          insurance_estimate: 'Insurance Estimate',
          plumber_report: 'Plumber Report',
        };
        return typeMap[type] || type;
      },
    },
    {
      title: 'Client Name',
      dataIndex: 'client_name',
      key: 'client_name',
      width: 150,
    },
    {
      title: 'Amount',
      dataIndex: 'total_amount',
      key: 'total_amount',
      width: 120,
      render: (amount: number) => `$${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {getStatusText(status)}
        </Tag>
      ),
    },
    {
      title: 'Created Date',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: 'Actions',
      key: 'action',
      width: 120,
      fixed: 'right' as const,
      render: (_: any, record: Document) => {
        const menuItems = [
          {
            key: 'view',
            icon: <EyeOutlined />,
            label: 'View',
            onClick: () => navigate(`/documents/${record.id}`),
          },
          {
            key: 'edit',
            icon: <EditOutlined />,
            label: 'Edit',
            onClick: () => {
              // Navigate to the appropriate edit page based on document type
              if (record.type === 'invoice') {
                navigate(`/invoices/${record.id}/edit`);
              } else if (record.type === 'estimate') {
                navigate(`/estimates/${record.id}/edit`);
              } else if (record.type === 'plumber_report') {
                navigate(`/plumber-reports/${record.id}/edit`);
              }
            },
          },
          {
            key: 'download',
            icon: <DownloadOutlined />,
            label: 'Download PDF',
            onClick: () => handleDownloadPDF(record.id),
          },
          {
            key: 'send',
            icon: <MailOutlined />,
            label: 'Send Email',
            onClick: () => navigate(`/documents/${record.id}/send`),
          },
          {
            key: 'duplicate',
            icon: <CopyOutlined />,
            label: 'Duplicate',
            onClick: () => duplicateMutation.mutate(record.id),
          },
          {
            type: 'divider' as const,
          },
          {
            key: 'delete',
            icon: <DeleteOutlined />,
            label: 'Delete',
            danger: true,
            onClick: () => handleDelete(record.id),
          },
        ];

        return (
          <Dropdown menu={{ items: menuItems }} trigger={['click']}>
            <Button icon={<MoreOutlined />} />
          </Dropdown>
        );
      },
    },
  ];

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2}>
            {type === 'estimate' && 'Estimate List'}
            {type === 'invoice' && 'Invoice List'}
            {type === 'insurance_estimate' && 'Insurance Estimate List'}
            {type === 'plumber_report' && 'Plumber Report List'}
            {!type && 'All Documents'}
          </Title>
        </Col>
        <Col>
          <Button type="primary" onClick={() => {
            const createPath = type === 'plumber_report' ? '/create/plumber' :
                               `/create/${type || 'estimate'}`;
            navigate(createPath);
          }}>
            Create New Document
          </Button>
        </Col>
      </Row>

      {/* Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Input
              placeholder="Enter search term"
              prefix={<SearchOutlined />}
              value={filter.search}
              onChange={(e) => setFilter({ ...filter, search: e.target.value })}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="Select status"
              style={{ width: '100%' }}
              allowClear
              value={filter.status}
              onChange={(value) => setFilter({ ...filter, status: value })}
            >
              <Select.Option value="draft">Draft</Select.Option>
              <Select.Option value="sent">Sent</Select.Option>
              <Select.Option value="paid">Paid</Select.Option>
              <Select.Option value="cancelled">Cancelled</Select.Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <RangePicker
              style={{ width: '100%' }}
              onChange={(dates) => {
                if (dates) {
                  setFilter({
                    ...filter,
                    date_from: dates[0]?.format('YYYY-MM-DD'),
                    date_to: dates[1]?.format('YYYY-MM-DD'),
                  });
                } else {
                  setFilter({
                    ...filter,
                    date_from: undefined,
                    date_to: undefined,
                  });
                }
              }}
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Space>
              <Button 
                icon={<FilterOutlined />}
                onClick={() => setCurrentPage(1)}
              >
                Apply Filter
              </Button>
              <Button 
                onClick={() => {
                  setFilter({ type: type as DocumentType });
                  setCurrentPage(1);
                }}
              >
                Reset
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={data?.items}  // Changed from data?.data to data?.items
          rowKey="id"
          loading={isLoading}
          pagination={{
            current: currentPage,
            pageSize: pageSize,
            total: data?.total,
            showSizeChanger: true,
            showTotal: (total) => `${total} total`,
            onChange: (page, size) => {
              setCurrentPage(page);
              setPageSize(size || 20);
            },
          }}
          scroll={{ x: 1000 }}
        />
      </Card>
    </div>
  );
};

export default DocumentList;