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
    label: 'Draft', 
    icon: <FileAddOutlined />,
    description: 'Work order is being drafted.'
  },
  pending: { 
    color: 'warning', 
    label: 'Pending Approval', 
    icon: <ClockCircleOutlined />,
    description: 'Waiting for customer approval.'
  },
  approved: { 
    color: 'blue', 
    label: 'Approved', 
    icon: <CheckCircleOutlined />,
    description: 'Customer has approved the work.'
  },
  in_progress: { 
    color: 'processing', 
    label: 'In Progress', 
    icon: <BuildOutlined />,
    description: 'Work is currently in progress.'
  },
  completed: { 
    color: 'success', 
    label: 'Completed', 
    icon: <CheckCircleOutlined />,
    description: 'Work has been completed.'
  },
  cancelled: { 
    color: 'error', 
    label: 'Cancelled', 
    icon: <ExclamationCircleOutlined />,
    description: 'Work has been cancelled.'
  },
} as const;

// Document type labels
const documentTypeLabels: Record<DocumentType, string> = {
  estimate: 'Estimate',
  invoice: 'Invoice',
  insurance_estimate: 'Insurance Estimate',
  plumber_report: 'Plumber Report',
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
      message.warning('Please enter a comment.');
      return;
    }
    onSubmit(comment.trim());
    setComment('');
  };

  return (
    <Modal
      title="Add Comment"
      open={visible}
      onCancel={onCancel}
      onOk={handleSubmit}
      confirmLoading={loading}
      okText="Add"
      cancelText="Cancel"
    >
      <TextArea
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        placeholder="Enter your comment..."
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
      message.success('Status has been updated.');
      queryClient.invalidateQueries({ queryKey: ['work-order', id] });
      setStatusChangeVisible(false);
    },
    onError: (error: any) => {
      message.error(error.message || 'Failed to update status.');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: workOrderService.deleteWorkOrder,
    onSuccess: () => {
      message.success('Work order has been deleted.');
      navigate('/work-orders');
    },
    onError: (error: any) => {
      message.error(error.message || 'Failed to delete.');
    },
  });

  // Add comment mutation
  const commentMutation = useMutation({
    mutationFn: (comment: string) =>
      workOrderService.addComment(id!, comment),
    onSuccess: () => {
      message.success('Comment has been added.');
      queryClient.invalidateQueries({ queryKey: ['work-order', id] });
      queryClient.invalidateQueries({ queryKey: ['work-order-activities', id] });
      setCommentModalVisible(false);
    },
    onError: (error: any) => {
      message.error(error.message || 'Failed to add comment.');
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
      title: 'Are you sure you want to delete this work order?',
      content: 'This action cannot be undone.',
      icon: <ExclamationCircleOutlined />,
      okText: 'Delete',
      okType: 'danger',
      cancelText: 'Cancel',
      onOk: () => deleteMutation.mutate(id!),
    });
  }, [deleteMutation, id]);

  const handlePrint = useCallback(() => {
    window.print();
  }, []);

  const handleSendNotification = useCallback(() => {
    message.info('Notification sending feature will be implemented soon.');
  }, []);

  const handleGeneratePDF = useCallback(() => {
    message.info('PDF generation feature will be implemented soon.');
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
      label: 'Generate PDF',
      onClick: handleGeneratePDF,
    },
    {
      key: 'send',
      icon: <SendOutlined />,
      label: 'Send Notification',
      onClick: handleSendNotification,
      disabled: workOrder?.status === 'draft',
    },
    {
      key: 'comment',
      icon: <MailOutlined />,
      label: 'Add Comment',
      onClick: () => setCommentModalVisible(true),
    },
    {
      type: 'divider',
    },
    {
      key: 'duplicate',
      icon: <FileAddOutlined />,
      label: 'Duplicate',
      onClick: () => message.info('Duplicate feature will be implemented soon.'),
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
        message="Error"
        description="Failed to load work order."
        type="error"
        showIcon
        action={
          <Button onClick={() => navigate('/work-orders')}>
            Back to List
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
                Back to List
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
                placeholder="Change Status"
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
                Edit
              </Button>
              <Button
                icon={<PrinterOutlined />}
                onClick={handlePrint}
              >
                Print
              </Button>
              <Dropdown menu={{ items: actionMenuItems }}>
                <Button icon={<MoreOutlined />} />
              </Dropdown>
              <Popconfirm
                title="Confirm Delete"
                description="Are you sure you want to delete this work order?"
                onConfirm={handleDelete}
                okText="Delete"
                cancelText="Cancel"
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
          <Card title="Company Information" style={{ marginBottom: 24 }}>
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
                  <Descriptions.Item label="Company Name">
                    <Text strong>{company?.name || 'Unknown Company'}</Text>
                  </Descriptions.Item>
                  <Descriptions.Item label="Company Code">
                    {company?.company_code || '-'}
                  </Descriptions.Item>
                  <Descriptions.Item label="Contact" span={2}>
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
                  <Descriptions.Item label="Address" span={2}>
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
          <Card title="Client Information" style={{ marginBottom: 24 }}>
            <Descriptions column={2} size="small">
              <Descriptions.Item label="Client Name">
                <Text strong>{workOrder.client_name}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Contact">
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
              <Descriptions.Item label="Service Address" span={2}>
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
          <Card title="Work Details" style={{ marginBottom: 24 }}>
            <Descriptions column={1} size="small">
              <Descriptions.Item label="Document Type">
                <Tag color="blue">{documentTypeLabels[workOrder.document_type]}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Selected Trades">
                <Space wrap>
                  {workOrder.trades.map((trade, index) => (
                    <Tag key={index} color="green">{trade}</Tag>
                  ))}
                </Space>
              </Descriptions.Item>
              {workOrder.work_description && (
                <Descriptions.Item label="Work Description">
                  <Paragraph>
                    <div dangerouslySetInnerHTML={{ __html: workOrder.work_description }} />
                  </Paragraph>
                </Descriptions.Item>
              )}
              {workOrder.consultation_notes && (
                <Descriptions.Item label="Phone Consultation Notes">
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
          <Card title="Summary Information" style={{ marginBottom: 24 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text>Final Cost:</Text>
                <Text strong style={{ fontSize: '18px', color: '#52c41a' }}>
                  ${workOrder.final_cost.toLocaleString()}
                </Text>
              </div>
              <Divider style={{ margin: '12px 0' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text>Created Date:</Text>
                <Space>
                  <CalendarOutlined />
                  <Text>{new Date(workOrder.created_at).toLocaleDateString('en-US')}</Text>
                </Space>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text>Created By:</Text>
                <Space>
                  <UserOutlined />
                  <Text>{workOrder.created_by_staff_name || '-'}</Text>
                </Space>
              </div>
              {workOrder.assigned_to_staff_name && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Text>Assigned To:</Text>
                  <Space>
                    <UserOutlined />
                    <Text>{workOrder.assigned_to_staff_name}</Text>
                  </Space>
                </div>
              )}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text>Last Updated:</Text>
                <Text type="secondary">
                  {new Date(workOrder.updated_at).toLocaleDateString('en-US')}
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
        title="Change Status"
        open={statusChangeVisible}
        onCancel={() => setStatusChangeVisible(false)}
        onOk={() => handleStatusConfirm()}
        confirmLoading={statusMutation.isPending}
        okText="Change"
        cancelText="Cancel"
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>Do you want to change the status to the following?</Text>
          <Space>
            <Text>Current:</Text>
            <Tag color={statusConfig[workOrder.status].color}>
              {statusConfig[workOrder.status].label}
            </Tag>
            <Text>→</Text>
            <Tag color={statusConfig[newStatus].color}>
              {statusConfig[newStatus].label}
            </Tag>
          </Space>
          <TextArea
            placeholder="Enter reason for change (optional)"
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