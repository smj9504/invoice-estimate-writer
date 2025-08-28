import React, { useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  Row,
  Col,
  Typography,
  Tag,
  Button,
  Space,
  Descriptions,
  Divider,
  Modal,
  message,
  Select,
  Input,
  Tooltip,
  Spin,
  Alert,
  Avatar,
  Dropdown,
  MenuProps,
  Popconfirm,
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  DeleteOutlined,
  PrinterOutlined,
  SendOutlined,
  FileTextOutlined,
  PhoneOutlined,
  MailOutlined,
  HomeOutlined,
  DollarOutlined,
  CalendarOutlined,
  UserOutlined,
  BuildOutlined,
  MoreOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  FileAddOutlined,
  CreditCardOutlined,
} from '@ant-design/icons';
import { WorkOrder, DocumentType } from '../types';
import { workOrderService } from '../services/workOrderService';
import { companyService } from '../services/companyService';
import ActivityTimeline from '../components/work-order/ActivityTimeline';
import PaymentSection from '../components/work-order/PaymentSection';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { confirm } = Modal;

// Status configuration
const statusConfig = {
  draft: { 
    color: 'default', 
    label: '초안', 
    icon: <FileAddOutlined />,
    description: '작업 지시서가 작성 중입니다.'
  },
  pending: { 
    color: 'warning', 
    label: '승인 대기', 
    icon: <ClockCircleOutlined />,
    description: '고객의 승인을 기다리고 있습니다.'
  },
  approved: { 
    color: 'blue', 
    label: '승인됨', 
    icon: <CheckCircleOutlined />,
    description: '고객이 작업을 승인했습니다.'
  },
  in_progress: { 
    color: 'processing', 
    label: '진행중', 
    icon: <BuildOutlined />,
    description: '작업이 진행되고 있습니다.'
  },
  completed: { 
    color: 'success', 
    label: '완료', 
    icon: <CheckCircleOutlined />,
    description: '작업이 완료되었습니다.'
  },
  cancelled: { 
    color: 'error', 
    label: '취소됨', 
    icon: <ExclamationCircleOutlined />,
    description: '작업이 취소되었습니다.'
  },
} as const;

// Document type labels
const documentTypeLabels: Record<DocumentType, string> = {
  estimate: '견적서',
  invoice: '인보이스',
  insurance_estimate: '보험 견적서',
  plumber_report: '배관공 보고서',
};

interface CommentModalProps {
  visible: boolean;
  onCancel: () => void;
  onSubmit: (comment: string) => void;
  loading?: boolean;
}

const CommentModal: React.FC<CommentModalProps> = ({
  visible,
  onCancel,
  onSubmit,
  loading = false,
}) => {
  const [comment, setComment] = useState('');

  const handleSubmit = () => {
    if (!comment.trim()) {
      message.warning('코멘트를 입력해주세요.');
      return;
    }
    onSubmit(comment.trim());
    setComment('');
  };

  return (
    <Modal
      title="코멘트 추가"
      open={visible}
      onCancel={onCancel}
      onOk={handleSubmit}
      confirmLoading={loading}
      okText="추가"
      cancelText="취소"
    >
      <TextArea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        placeholder="코멘트를 입력하세요..."
        rows={4}
        maxLength={500}
        showCount
      />
    </Modal>
  );
};

const WorkOrderDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  const [statusChangeVisible, setStatusChangeVisible] = useState(false);
  const [newStatus, setNewStatus] = useState<WorkOrder['status']>('draft');
  const [commentModalVisible, setCommentModalVisible] = useState(false);

  // Fetch work order details
  const {
    data: workOrder,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['work-order', id],
    queryFn: () => workOrderService.getWorkOrder(id!),
    enabled: !!id,
  });

  // Fetch company details
  const { data: company } = useQuery({
    queryKey: ['company', workOrder?.company_id],
    queryFn: () => companyService.getCompany(workOrder!.company_id),
    enabled: !!workOrder?.company_id,
  });

  // Status update mutation
  const statusMutation = useMutation({
    mutationFn: ({ status, comment }: { status: WorkOrder['status']; comment?: string }) =>
      workOrderService.updateWorkOrderStatus(id!, status, comment),
    onSuccess: () => {
      message.success('상태가 업데이트되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['work-order', id] });
      setStatusChangeVisible(false);
    },
    onError: (error: any) => {
      message.error(error.message || '상태 업데이트에 실패했습니다.');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: workOrderService.deleteWorkOrder,
    onSuccess: () => {
      message.success('작업 지시서가 삭제되었습니다.');
      navigate('/work-orders');
    },
    onError: (error: any) => {
      message.error(error.message || '삭제에 실패했습니다.');
    },
  });

  // Add comment mutation
  const commentMutation = useMutation({
    mutationFn: (comment: string) =>
      workOrderService.addComment(id!, comment),
    onSuccess: () => {
      message.success('코멘트가 추가되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['work-order', id] });
      queryClient.invalidateQueries({ queryKey: ['work-order-activities', id] });
      setCommentModalVisible(false);
    },
    onError: (error: any) => {
      message.error(error.message || '코멘트 추가에 실패했습니다.');
    },
  });

  const handleStatusChange = useCallback((status: WorkOrder['status']) => {
    setNewStatus(status);
    setStatusChangeVisible(true);
  }, []);

  const handleStatusConfirm = useCallback((comment?: string) => {
    statusMutation.mutate({ status: newStatus, comment });
  }, [statusMutation, newStatus]);

  const handleDelete = useCallback(() => {
    confirm({
      title: '작업 지시서를 삭제하시겠습니까?',
      content: '이 작업은 되돌릴 수 없습니다.',
      icon: <ExclamationCircleOutlined />,
      okText: '삭제',
      okType: 'danger',
      cancelText: '취소',
      onOk: () => deleteMutation.mutate(id!),
    });
  }, [deleteMutation, id]);

  const handlePrint = useCallback(() => {
    window.print();
  }, []);

  const handleSendNotification = useCallback(() => {
    message.info('알림 발송 기능은 곧 구현될 예정입니다.');
  }, []);

  const handleGeneratePDF = useCallback(() => {
    message.info('PDF 생성 기능은 곧 구현될 예정입니다.');
  }, []);

  // Get available status transitions
  const getAvailableStatuses = useCallback((currentStatus: WorkOrder['status']) => {
    const allStatuses: WorkOrder['status'][] = [
      'draft', 'pending', 'approved', 'in_progress', 'completed', 'cancelled'
    ];
    return allStatuses.filter(status => status !== currentStatus);
  }, []);

  // Action menu items
  const actionMenuItems: MenuProps['items'] = [
    {
      key: 'pdf',
      icon: <FileTextOutlined />,
      label: 'PDF 생성',
      onClick: handleGeneratePDF,
    },
    {
      key: 'send',
      icon: <SendOutlined />,
      label: '알림 발송',
      onClick: handleSendNotification,
      disabled: workOrder?.status === 'draft',
    },
    {
      key: 'comment',
      icon: <MailOutlined />,
      label: '코멘트 추가',
      onClick: () => setCommentModalVisible(true),
    },
    {
      type: 'divider',
    },
    {
      key: 'duplicate',
      icon: <FileAddOutlined />,
      label: '복제하기',
      onClick: () => message.info('복제 기능은 곧 구현될 예정입니다.'),
    },
  ];

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error || !workOrder) {
    return (
      <Alert
        message="오류"
        description="작업 지시서를 불러오는데 실패했습니다."
        type="error"
        showIcon
        action={
          <Button onClick={() => navigate('/work-orders')}>
            목록으로 돌아가기
          </Button>
        }
      />
    );
  }

  const currentStatusConfig = statusConfig[workOrder.status];

  return (
    <div className="work-order-detail" style={{ padding: '0 0 24px 0' }}>
      {/* Header Section */}
      <Card style={{ marginBottom: 24 }} className="no-print">
        <Row justify="space-between" align="middle">
          <Col>
            <Space align="center">
              <Button
                icon={<ArrowLeftOutlined />}
                onClick={() => navigate('/work-orders')}
              >
                목록으로
              </Button>
              <Divider type="vertical" />
              <Space direction="vertical" size={0}>
                <Title level={2} style={{ margin: 0 }}>
                  {workOrder.work_order_number}
                </Title>
                <Space align="center">
                  <Tag
                    color={currentStatusConfig.color}
                    icon={currentStatusConfig.icon}
                    style={{ fontSize: '14px', padding: '4px 12px' }}
                  >
                    {currentStatusConfig.label}
                  </Tag>
                  <Text type="secondary">
                    {currentStatusConfig.description}
                  </Text>
                </Space>
              </Space>
            </Space>
          </Col>
          <Col>
            <Space>
              <Select
                value={workOrder.status}
                onChange={handleStatusChange}
                style={{ width: 120 }}
                placeholder="상태 변경"
              >
                {getAvailableStatuses(workOrder.status).map(status => (
                  <Select.Option key={status} value={status}>
                    <Space>
                      {statusConfig[status].icon}
                      {statusConfig[status].label}
                    </Space>
                  </Select.Option>
                ))}
              </Select>
              <Button
                icon={<EditOutlined />}
                onClick={() => navigate(`/work-orders/${id}/edit`)}
              >
                편집
              </Button>
              <Button
                icon={<PrinterOutlined />}
                onClick={handlePrint}
              >
                인쇄
              </Button>
              <Dropdown menu={{ items: actionMenuItems }}>
                <Button icon={<MoreOutlined />} />
              </Dropdown>
              <Popconfirm
                title="삭제 확인"
                description="정말로 이 작업 지시서를 삭제하시겠습니까?"
                onConfirm={handleDelete}
                okText="삭제"
                cancelText="취소"
                okType="danger"
              >
                <Button danger icon={<DeleteOutlined />} />
              </Popconfirm>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Main Content */}
      <Row gutter={[24, 24]}>
        {/* Left Column */}
        <Col xs={24} lg={16}>
          {/* Company Information */}
          <Card title="회사 정보" style={{ marginBottom: 24 }}>
            <Row gutter={16}>
              <Col span={4}>
                <Avatar
                  size={64}
                  src={company?.logo}
                  icon={<BuildOutlined />}
                  style={{ backgroundColor: '#1890ff' }}
                />
              </Col>
              <Col span={20}>
                <Descriptions column={2} size="small">
                  <Descriptions.Item label="회사명">
                    <Text strong>{company?.name || 'Unknown Company'}</Text>
                  </Descriptions.Item>
                  <Descriptions.Item label="회사코드">
                    {company?.company_code || '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="연락처" span={2}>
                    <Space split={<Divider type="vertical" />}>
                      {company?.phone && (
                        <Space>
                          <PhoneOutlined />
                          <Text copyable>{company.phone}</Text>
                        </Space>
                      )}
                      {company?.email && (
                        <Space>
                          <MailOutlined />
                          <Text copyable>{company.email}</Text>
                        </Space>
                      )}
                    </Space>
                  </Descriptions.Item>
                  <Descriptions.Item label="주소" span={2}>
                    <Space>
                      <HomeOutlined />
                      <Text>
                        {[company?.address, company?.city, company?.state, company?.zipcode]
                          .filter(Boolean)
                          .join(', ') || '-'}
                      </Text>
                    </Space>
                  </Descriptions.Item>
                </Descriptions>
              </Col>
            </Row>
          </Card>

          {/* Client Information */}
          <Card title="고객 정보" style={{ marginBottom: 24 }}>
            <Descriptions column={2} size="small">
              <Descriptions.Item label="고객명">
                <Text strong>{workOrder.client_name}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="연락처">
                <Space split={<Divider type="vertical" />}>
                  {workOrder.client_phone && (
                    <Space>
                      <PhoneOutlined />
                      <Text copyable>{workOrder.client_phone}</Text>
                    </Space>
                  )}
                  {workOrder.client_email && (
                    <Space>
                      <MailOutlined />
                      <Text copyable>{workOrder.client_email}</Text>
                    </Space>
                  )}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="서비스 주소" span={2}>
                <Space>
                  <HomeOutlined />
                  <Text>
                    {[
                      workOrder.client_address,
                      workOrder.client_city,
                      workOrder.client_state,
                      workOrder.client_zipcode
                    ].filter(Boolean).join(', ') || '-'}
                  </Text>
                </Space>
              </Descriptions.Item>
            </Descriptions>
          </Card>

          {/* Work Details */}
          <Card title="작업 상세" style={{ marginBottom: 24 }}>
            <Descriptions column={1} size="small">
              <Descriptions.Item label="문서 타입">
                <Tag color="blue">{documentTypeLabels[workOrder.document_type]}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="선택된 업종">
                <Space wrap>
                  {workOrder.trades.map((trade, index) => (
                    <Tag key={index} color="green">{trade}</Tag>
                  ))}
                </Space>
              </Descriptions.Item>
              {workOrder.work_description && (
                <Descriptions.Item label="작업 설명">
                  <Paragraph>
                    <div dangerouslySetInnerHTML={{ __html: workOrder.work_description }} />
                  </Paragraph>
                </Descriptions.Item>
              )}
              {workOrder.consultation_notes && (
                <Descriptions.Item label="전화 상담 메모">
                  <Paragraph>
                    {workOrder.consultation_notes}
                  </Paragraph>
                </Descriptions.Item>
              )}
            </Descriptions>
          </Card>

          {/* Payment Section */}
          <PaymentSection workOrder={workOrder} />
        </Col>

        {/* Right Column */}
        <Col xs={24} lg={8}>
          {/* Quick Info */}
          <Card title="요약 정보" style={{ marginBottom: 24 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text>최종 비용:</Text>
                <Text strong style={{ fontSize: '18px', color: '#52c41a' }}>
                  ${workOrder.final_cost.toLocaleString()}
                </Text>
              </div>
              <Divider style={{ margin: '12px 0' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text>생성일:</Text>
                <Space>
                  <CalendarOutlined />
                  <Text>{new Date(workOrder.created_at).toLocaleDateString('ko-KR')}</Text>
                </Space>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text>생성자:</Text>
                <Space>
                  <UserOutlined />
                  <Text>{workOrder.created_by_staff_name || '-'}</Text>
                </Space>
              </div>
              {workOrder.assigned_to_staff_name && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Text>담당자:</Text>
                  <Space>
                    <UserOutlined />
                    <Text>{workOrder.assigned_to_staff_name}</Text>
                  </Space>
                </div>
              )}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text>최종 수정:</Text>
                <Text type="secondary">
                  {new Date(workOrder.updated_at).toLocaleDateString('ko-KR')}
                </Text>
              </div>
            </Space>
          </Card>

          {/* Activity Timeline */}
          <ActivityTimeline workOrderId={id!} />
        </Col>
      </Row>

      {/* Status Change Modal */}
      <Modal
        title="상태 변경"
        open={statusChangeVisible}
        onCancel={() => setStatusChangeVisible(false)}
        onOk={() => handleStatusConfirm()}
        confirmLoading={statusMutation.isPending}
        okText="변경"
        cancelText="취소"
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>상태를 다음으로 변경하시겠습니까?</Text>
          <Space>
            <Text>현재:</Text>
            <Tag color={statusConfig[workOrder.status].color}>
              {statusConfig[workOrder.status].label}
            </Tag>
            <Text>→</Text>
            <Tag color={statusConfig[newStatus].color}>
              {statusConfig[newStatus].label}
            </Tag>
          </Space>
          <TextArea
            placeholder="변경 사유를 입력하세요 (선택사항)"
            rows={3}
            onChange={(e) => {
              // Handle comment if needed
            }}
          />
        </Space>
      </Modal>

      {/* Comment Modal */}
      <CommentModal
        visible={commentModalVisible}
        onCancel={() => setCommentModalVisible(false)}
        onSubmit={(comment) => commentMutation.mutate(comment)}
        loading={commentMutation.isPending}
      />

      {/* Print Styles */}
      <style>{`
        @media print {
          .no-print {
            display: none !important;
          }
          .work-order-detail {
            padding: 0 !important;
          }
          .ant-card {
            border: none !important;
            box-shadow: none !important;
          }
          .ant-card-body {
            padding: 16px 0 !important;
          }
        }
      `}</style>
    </div>
  );
};

export default WorkOrderDetail;