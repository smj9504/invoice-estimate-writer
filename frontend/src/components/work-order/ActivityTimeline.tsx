import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, Timeline, Typography, Space, Tag, Avatar, Empty, Spin, Alert } from 'antd';
import {
  ClockCircleOutlined,
  UserOutlined,
  FileTextOutlined,
  EditOutlined,
  CheckCircleOutlined,
  MessageOutlined,
  SendOutlined,
  PhoneOutlined,
  MailOutlined,
  ExclamationCircleOutlined,
  BuildOutlined,
  FileAddOutlined,
  CreditCardOutlined,
} from '@ant-design/icons';
import { workOrderService } from '../../services/workOrderService';

const { Text, Title } = Typography;

interface ActivityItem {
  id: string;
  type: 'status_change' | 'comment' | 'email_sent' | 'phone_call' | 'document_generated' | 'payment' | 'system';
  title: string;
  description?: string;
  user_name?: string;
  user_avatar?: string;
  created_at: string;
  metadata?: Record<string, any>;
}

interface ActivityTimelineProps {
  workOrderId: string;
}

// Activity type configurations
const activityConfig = {
  status_change: {
    icon: <CheckCircleOutlined />,
    color: '#1890ff',
    getTitle: (item: ActivityItem) => '상태 변경',
    getDescription: (item: ActivityItem) => 
      item.metadata?.from && item.metadata?.to 
        ? `${item.metadata.from} → ${item.metadata.to}`
        : item.description,
  },
  comment: {
    icon: <MessageOutlined />,
    color: '#52c41a',
    getTitle: (item: ActivityItem) => '코멘트 추가',
    getDescription: (item: ActivityItem) => item.description,
  },
  email_sent: {
    icon: <MailOutlined />,
    color: '#722ed1',
    getTitle: (item: ActivityItem) => '이메일 발송',
    getDescription: (item: ActivityItem) => 
      `${item.metadata?.recipient || '고객'}에게 ${item.metadata?.type || '알림'} 이메일 발송`,
  },
  phone_call: {
    icon: <PhoneOutlined />,
    color: '#fa8c16',
    getTitle: (item: ActivityItem) => '전화 상담',
    getDescription: (item: ActivityItem) => item.description,
  },
  document_generated: {
    icon: <FileTextOutlined />,
    color: '#13c2c2',
    getTitle: (item: ActivityItem) => '문서 생성',
    getDescription: (item: ActivityItem) => 
      `${item.metadata?.document_type || 'PDF'} 문서가 생성되었습니다`,
  },
  payment: {
    icon: <CreditCardOutlined />,
    color: '#52c41a',
    getTitle: (item: ActivityItem) => '결제 처리',
    getDescription: (item: ActivityItem) => 
      `${item.metadata?.amount ? `$${item.metadata.amount}` : ''} ${item.metadata?.payment_method || ''} 결제`,
  },
  system: {
    icon: <BuildOutlined />,
    color: '#8c8c8c',
    getTitle: (item: ActivityItem) => '시스템',
    getDescription: (item: ActivityItem) => item.description,
  },
} as const;

// Status color mapping
const statusColors: Record<string, string> = {
  draft: '#d9d9d9',
  pending: '#faad14',
  approved: '#1890ff',
  in_progress: '#722ed1',
  completed: '#52c41a',
  cancelled: '#ff4d4f',
};

const ActivityTimeline: React.FC<ActivityTimelineProps> = ({ workOrderId }) => {
  // Fetch activity data
  const {
    data: activities = [],
    isLoading,
    error,
  } = useQuery({
    queryKey: ['work-order-activities', workOrderId],
    queryFn: () => workOrderService.getWorkOrderActivities(workOrderId),
    enabled: !!workOrderId,
  });

  if (isLoading) {
    return (
      <Card title="활동 내역" style={{ height: '400px' }}>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '300px' }}>
          <Spin size="large" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card title="활동 내역">
        <Alert
          message="오류"
          description="활동 내역을 불러오는데 실패했습니다."
          type="error"
          showIcon
        />
      </Card>
    );
  }

  if (activities.length === 0) {
    return (
      <Card title="활동 내역">
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="활동 내역이 없습니다"
        />
      </Card>
    );
  }

  const getActivityConfig = (type: ActivityItem['type']) => {
    return activityConfig[type] || activityConfig.system;
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) {
      const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
      return diffInMinutes < 1 ? '방금 전' : `${diffInMinutes}분 전`;
    } else if (diffInHours < 24) {
      return `${diffInHours}시간 전`;
    } else {
      return date.toLocaleDateString('ko-KR');
    }
  };

  const timelineItems = activities.map((activity) => {
    const config = getActivityConfig(activity.type);
    const isStatusChange = activity.type === 'status_change';
    
    return {
      dot: (
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: '50%',
            backgroundColor: config.color,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: '14px',
          }}
        >
          {config.icon}
        </div>
      ),
      children: (
        <div style={{ paddingBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
            <div style={{ flex: 1 }}>
              <Space align="center">
                <Text strong>{config.getTitle(activity)}</Text>
                {isStatusChange && activity.metadata?.to && (
                  <Tag 
                    color={statusColors[activity.metadata.to] || '#d9d9d9'}
                    style={{ marginLeft: 8 }}
                  >
                    {activity.metadata.to_label || activity.metadata.to}
                  </Tag>
                )}
              </Space>
              {config.getDescription(activity) && (
                <div style={{ marginTop: 4 }}>
                  <Text type="secondary" style={{ fontSize: '13px' }}>
                    {config.getDescription(activity)}
                  </Text>
                </div>
              )}
            </div>
            <div style={{ textAlign: 'right', marginLeft: 16 }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {formatTimeAgo(activity.created_at)}
              </Text>
              <div style={{ marginTop: 2 }}>
                <Space size="small" align="center">
                  <Avatar 
                    size={20} 
                    src={activity.user_avatar}
                    icon={<UserOutlined />}
                  />
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    {activity.user_name || '시스템'}
                  </Text>
                </Space>
              </div>
            </div>
          </div>
          
          {/* Additional metadata display */}
          {activity.metadata && (
            <div style={{ marginTop: 8 }}>
              {activity.metadata.reason && (
                <div style={{ padding: '8px 12px', backgroundColor: '#f5f5f5', borderRadius: '6px', marginTop: 8 }}>
                  <Text style={{ fontSize: '13px', fontStyle: 'italic' }}>
                    사유: {activity.metadata.reason}
                  </Text>
                </div>
              )}
              
              {activity.metadata.attachments && activity.metadata.attachments.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <Space wrap>
                    {activity.metadata.attachments.map((attachment: any, index: number) => (
                      <Tag key={index} icon={<FileTextOutlined />}>
                        {attachment.name}
                      </Tag>
                    ))}
                  </Space>
                </div>
              )}
            </div>
          )}
        </div>
      ),
    };
  });

  return (
    <Card 
      title={
        <Space>
          <ClockCircleOutlined />
          활동 내역
          <Tag color="blue">{activities.length}</Tag>
        </Space>
      }
      style={{ maxHeight: '600px', overflow: 'auto' }}
    >
      <Timeline
        items={timelineItems}
        mode="left"
        style={{ paddingTop: 8 }}
      />
    </Card>
  );
};

export default ActivityTimeline;