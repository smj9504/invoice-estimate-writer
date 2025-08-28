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
      message.success('서류가 삭제되었습니다');
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: () => {
      message.error('삭제 중 오류가 발생했습니다');
    },
  });

  // Duplicate mutation
  const duplicateMutation = useMutation({
    mutationFn: documentService.duplicateDocument,
    onSuccess: () => {
      message.success('서류가 복제되었습니다');
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: () => {
      message.error('복제 중 오류가 발생했습니다');
    },
  });

  const handleDelete = (id: string) => {
    Modal.confirm({
      title: '서류 삭제',
      content: '이 서류를 삭제하시겠습니까?',
      okText: '삭제',
      cancelText: '취소',
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
      message.error('PDF 다운로드 중 오류가 발생했습니다');
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
      case 'draft': return '임시저장';
      case 'sent': return '발송됨';
      case 'paid': return '결제완료';
      case 'cancelled': return '취소됨';
      default: return status;
    }
  };

  const columns = [
    {
      title: '문서번호',
      dataIndex: 'document_number',
      key: 'document_number',
      width: 150,
    },
    {
      title: '유형',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (type: DocumentType) => {
        const typeMap = {
          estimate: '견적서',
          invoice: '인보이스',
          insurance_estimate: '보험 견적서',
          plumber_report: '배관공 보고서',
        };
        return typeMap[type] || type;
      },
    },
    {
      title: '고객명',
      dataIndex: 'client_name',
      key: 'client_name',
      width: 150,
    },
    {
      title: '금액',
      dataIndex: 'total_amount',
      key: 'total_amount',
      width: 120,
      render: (amount: number) => `$${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
    },
    {
      title: '상태',
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
      title: '생성일',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '작업',
      key: 'action',
      width: 120,
      fixed: 'right' as const,
      render: (_: any, record: Document) => {
        const menuItems = [
          {
            key: 'view',
            icon: <EyeOutlined />,
            label: '보기',
            onClick: () => navigate(`/documents/${record.id}`),
          },
          {
            key: 'edit',
            icon: <EditOutlined />,
            label: '수정',
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
            label: 'PDF 다운로드',
            onClick: () => handleDownloadPDF(record.id),
          },
          {
            key: 'send',
            icon: <MailOutlined />,
            label: '이메일 발송',
            onClick: () => navigate(`/documents/${record.id}/send`),
          },
          {
            key: 'duplicate',
            icon: <CopyOutlined />,
            label: '복제',
            onClick: () => duplicateMutation.mutate(record.id),
          },
          {
            type: 'divider' as const,
          },
          {
            key: 'delete',
            icon: <DeleteOutlined />,
            label: '삭제',
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
            {type === 'estimate' && '견적서 목록'}
            {type === 'invoice' && '인보이스 목록'}
            {type === 'insurance_estimate' && '보험 견적서 목록'}
            {type === 'plumber_report' && '배관공 보고서 목록'}
            {!type && '전체 서류'}
          </Title>
        </Col>
        <Col>
          <Button type="primary" onClick={() => {
            const createPath = type === 'plumber_report' ? '/create/plumber' :
                               `/create/${type || 'estimate'}`;
            navigate(createPath);
          }}>
            새 서류 작성
          </Button>
        </Col>
      </Row>

      {/* Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Input
              placeholder="검색어 입력"
              prefix={<SearchOutlined />}
              value={filter.search}
              onChange={(e) => setFilter({ ...filter, search: e.target.value })}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="상태 선택"
              style={{ width: '100%' }}
              allowClear
              value={filter.status}
              onChange={(value) => setFilter({ ...filter, status: value })}
            >
              <Select.Option value="draft">임시저장</Select.Option>
              <Select.Option value="sent">발송됨</Select.Option>
              <Select.Option value="paid">결제완료</Select.Option>
              <Select.Option value="cancelled">취소됨</Select.Option>
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
                필터 적용
              </Button>
              <Button 
                onClick={() => {
                  setFilter({ type: type as DocumentType });
                  setCurrentPage(1);
                }}
              >
                초기화
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
            showTotal: (total) => `총 ${total}개`,
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