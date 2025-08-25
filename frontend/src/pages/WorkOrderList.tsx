import React, { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  message,
  Popconfirm,
  Typography,
  Row,
  Col,
  Tooltip,
  Select,
  Dropdown,
  MenuProps,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  SendOutlined,
  ExportOutlined,
  FileTextOutlined,
  MoreOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { WorkOrder, DocumentType } from '../types';
import { workOrderService } from '../services/workOrderService';
import { companyService } from '../services/companyService';
import WorkOrderFilters from '../components/work-order/WorkOrderFilters';
import WorkOrderStats from '../components/work-order/WorkOrderStats';
import type { ColumnsType } from 'antd/es/table';
import { saveAs } from 'file-saver';
import * as XLSX from 'xlsx';

const { Title } = Typography;
const { confirm } = Modal;

// Status configuration
const statusConfig = {
  draft: { color: 'default', label: '초안' },
  pending: { color: 'warning', label: '승인 대기' },
  approved: { color: 'blue', label: '승인됨' },
  in_progress: { color: 'processing', label: '진행중' },
  completed: { color: 'success', label: '완료' },
  cancelled: { color: 'error', label: '취소됨' },
} as const;

// Document type labels
const documentTypeLabels: Record<DocumentType, string> = {
  estimate: '견적서',
  invoice: '인보이스',
  insurance_estimate: '보험 견적서',
  plumber_report: '배관공 보고서',
};

interface WorkOrderListFilters {
  search?: string;
  status?: WorkOrder['status'];
  company_id?: string;
  document_type?: DocumentType;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

const WorkOrderList: React.FC = () => {
  const [filters, setFilters] = useState<WorkOrderListFilters>({
    page: 1,
    page_size: 10,
  });
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Fetch work orders
  const {
    data: workOrdersData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['work-orders', filters],
    queryFn: () => workOrderService.searchWorkOrders(filters),
    placeholderData: (previousData) => previousData,
  });

  // Fetch companies for company names
  const { data: companies = [] } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companyService.getCompanies(),
  });

  // Delete work order mutation
  const deleteMutation = useMutation({
    mutationFn: workOrderService.deleteWorkOrder,
    onSuccess: () => {
      message.success('작업 지시서가 삭제되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['work-orders'] });
      setSelectedRowKeys([]);
    },
    onError: (error: any) => {
      message.error(error.message || '삭제에 실패했습니다.');
    },
  });

  // Update status mutation
  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: WorkOrder['status'] }) =>
      workOrderService.updateWorkOrderStatus(id, status),
    onSuccess: () => {
      message.success('상태가 업데이트되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['work-orders'] });
    },
    onError: (error: any) => {
      message.error(error.message || '상태 업데이트에 실패했습니다.');
    },
  });

  const workOrders = workOrdersData?.items || [];
  const total = workOrdersData?.total || 0;

  // Get company name by ID
  const getCompanyName = useCallback((companyId: string) => {
    const company = companies.find(c => c.id === companyId);
    return company?.name || 'Unknown Company';
  }, [companies]);

  // Handle filter changes
  const handleFilterChange = useCallback((newFilters: Partial<WorkOrderListFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters, page: 1 }));
  }, []);

  // Handle pagination
  const handleTableChange = useCallback((pagination: any) => {
    setFilters(prev => ({
      ...prev,
      page: pagination.current,
      page_size: pagination.pageSize,
    }));
  }, []);

  // Handle actions
  const handleView = useCallback((record: WorkOrder) => {
    navigate(`/work-orders/${record.id}`);
  }, [navigate]);

  const handleEdit = useCallback((record: WorkOrder) => {
    navigate(`/work-orders/${record.id}/edit`);
  }, [navigate]);

  const handleDelete = useCallback((id: string) => {
    confirm({
      title: '작업 지시서를 삭제하시겠습니까?',
      content: '이 작업은 되돌릴 수 없습니다.',
      okText: '삭제',
      okType: 'danger',
      cancelText: '취소',
      onOk: () => deleteMutation.mutate(id),
    });
  }, [deleteMutation]);

  const handleStatusChange = useCallback((id: string, status: WorkOrder['status']) => {
    statusMutation.mutate({ id, status });
  }, [statusMutation]);

  // Export to Excel
  const handleExport = useCallback(() => {
    if (workOrders.length === 0) {
      message.warning('내보낼 데이터가 없습니다.');
      return;
    }

    const exportData = workOrders.map(order => ({
      '작업지시서번호': order.work_order_number,
      '회사명': getCompanyName(order.company_id),
      '문서타입': documentTypeLabels[order.document_type],
      '고객명': order.client_name,
      '상태': statusConfig[order.status].label,
      '최종비용': order.final_cost,
      '생성일': new Date(order.created_at).toLocaleDateString('ko-KR'),
      '생성자': order.created_by_staff_name || '-',
    }));

    const ws = XLSX.utils.json_to_sheet(exportData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, '작업지시서목록');
    
    const excelBuffer = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
    const blob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    saveAs(blob, `작업지시서목록_${new Date().toISOString().split('T')[0]}.xlsx`);
  }, [workOrders, getCompanyName]);

  // Status dropdown items
  const getStatusDropdownItems = useCallback((record: WorkOrder): MenuProps['items'] => {
    const statusOptions: WorkOrder['status'][] = ['draft', 'pending', 'approved', 'in_progress', 'completed', 'cancelled'];
    
    return statusOptions
      .filter(status => status !== record.status)
      .map(status => ({
        key: status,
        label: statusConfig[status].label,
        onClick: () => handleStatusChange(record.id, status),
      }));
  }, [handleStatusChange]);

  // Table columns
  const columns: ColumnsType<WorkOrder> = [
    {
      title: '작업지시서 번호',
      dataIndex: 'work_order_number',
      key: 'work_order_number',
      fixed: 'left',
      width: 150,
      render: (text: string, record: WorkOrder) => (
        <Button
          type="link"
          onClick={() => handleView(record)}
          style={{ padding: 0, height: 'auto' }}
        >
          {text}
        </Button>
      ),
    },
    {
      title: '회사명',
      dataIndex: 'company_id',
      key: 'company_id',
      width: 150,
      render: (companyId: string) => getCompanyName(companyId),
    },
    {
      title: '문서 타입',
      dataIndex: 'document_type',
      key: 'document_type',
      width: 120,
      render: (type: DocumentType) => (
        <Tag color="blue">{documentTypeLabels[type]}</Tag>
      ),
    },
    {
      title: '고객명',
      dataIndex: 'client_name',
      key: 'client_name',
      width: 150,
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: WorkOrder['status'], record: WorkOrder) => (
        <Dropdown
          menu={{ items: getStatusDropdownItems(record) }}
          trigger={['click']}
        >
          <Tag
            color={statusConfig[status].color}
            style={{ cursor: 'pointer' }}
          >
            {statusConfig[status].label}
          </Tag>
        </Dropdown>
      ),
    },
    {
      title: '최종 비용',
      dataIndex: 'final_cost',
      key: 'final_cost',
      width: 120,
      align: 'right',
      render: (cost: number) => `$${cost.toLocaleString()}`,
    },
    {
      title: '생성일',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date: string) => new Date(date).toLocaleDateString('ko-KR'),
    },
    {
      title: '생성자',
      dataIndex: 'created_by_staff_name',
      key: 'created_by_staff_name',
      width: 100,
      render: (name: string) => name || '-',
    },
    {
      title: '작업',
      key: 'actions',
      fixed: 'right',
      width: 120,
      render: (_, record: WorkOrder) => (
        <Space size="small">
          <Tooltip title="보기">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleView(record)}
            />
          </Tooltip>
          <Tooltip title="편집">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="삭제">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record.id)}
            />
          </Tooltip>
          <Dropdown
            menu={{
              items: [
                {
                  key: 'send',
                  icon: <SendOutlined />,
                  label: '발송',
                  disabled: record.status === 'draft',
                },
                {
                  key: 'duplicate',
                  icon: <FileTextOutlined />,
                  label: '복제',
                },
              ],
            }}
          >
            <Button type="text" icon={<MoreOutlined />} />
          </Dropdown>
        </Space>
      ),
    },
  ];

  return (
    <div>
      {/* Header */}
      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <FileTextOutlined style={{ fontSize: 24, marginRight: 12, color: '#1890ff' }} />
            <div>
              <Title level={2} style={{ margin: 0 }}>
                작업 지시서 목록
              </Title>
              <p style={{ margin: '4px 0 0 0', color: '#666' }}>
                모든 작업 지시서를 관리하고 추적합니다.
              </p>
            </div>
          </div>
          <Space>
            <Button
              icon={<ExportOutlined />}
              onClick={handleExport}
              disabled={workOrders.length === 0}
            >
              Excel 내보내기
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => navigate('/work-orders/new')}
            >
              새 작업 지시서
            </Button>
          </Space>
        </div>
      </Card>

      {/* Statistics Cards */}
      <WorkOrderStats workOrders={workOrders} />

      {/* Filters */}
      <WorkOrderFilters
        filters={filters}
        onFilterChange={handleFilterChange}
        companies={companies}
      />

      {/* Table */}
      <Card style={{ marginTop: 24 }}>
        <Table
          columns={columns}
          dataSource={workOrders}
          rowKey="id"
          loading={isLoading}
          pagination={{
            current: filters.page,
            pageSize: filters.page_size,
            total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `${range[0]}-${range[1]} / 총 ${total}개`,
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
          rowSelection={{
            selectedRowKeys,
            onChange: setSelectedRowKeys,
            selections: [
              Table.SELECTION_ALL,
              Table.SELECTION_INVERT,
              Table.SELECTION_NONE,
            ],
          }}
          size="small"
        />
      </Card>

      {/* Bulk Actions */}
      {selectedRowKeys.length > 0 && (
        <Card
          style={{
            position: 'fixed',
            bottom: 24,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 1000,
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          }}
        >
          <Space>
            <span>{selectedRowKeys.length}개 선택됨</span>
            <Button size="small" onClick={() => setSelectedRowKeys([])}>
              선택 해제
            </Button>
            <Button
              size="small"
              danger
              onClick={() => {
                confirm({
                  title: `${selectedRowKeys.length}개의 작업 지시서를 삭제하시겠습니까?`,
                  content: '이 작업은 되돌릴 수 없습니다.',
                  okText: '삭제',
                  okType: 'danger',
                  cancelText: '취소',
                  onOk: async () => {
                    for (const id of selectedRowKeys) {
                      await deleteMutation.mutateAsync(id as string);
                    }
                    setSelectedRowKeys([]);
                  },
                });
              }}
            >
              선택 항목 삭제
            </Button>
          </Space>
        </Card>
      )}
    </div>
  );
};

export default WorkOrderList;