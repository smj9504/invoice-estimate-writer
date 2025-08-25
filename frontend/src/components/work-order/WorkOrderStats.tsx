import React, { useMemo } from 'react';
import { Row, Col, Card, Statistic, Typography } from 'antd';
import {
  FileTextOutlined,
  ClockCircleOutlined,
  CalendarOutlined,
  DollarOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { WorkOrder } from '../../types';

const { Text } = Typography;

interface WorkOrderStatsProps {
  workOrders: WorkOrder[];
}

const WorkOrderStats: React.FC<WorkOrderStatsProps> = ({ workOrders }) => {
  const stats = useMemo(() => {
    const now = new Date();
    const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    
    // Total work orders
    const total = workOrders.length;
    
    // Pending approval count
    const pendingCount = workOrders.filter(wo => wo.status === 'pending').length;
    
    // This week's orders
    const thisWeekCount = workOrders.filter(wo => {
      const createdAt = new Date(wo.created_at);
      return createdAt >= oneWeekAgo;
    }).length;
    
    // Total revenue (completed orders only)
    const totalRevenue = workOrders
      .filter(wo => wo.status === 'completed')
      .reduce((sum, wo) => sum + wo.final_cost, 0);
    
    // Status distribution
    const statusCounts = workOrders.reduce((acc, wo) => {
      acc[wo.status] = (acc[wo.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    // High priority orders
    const highPriorityCount = workOrders.filter(wo => 
      wo.status === 'pending' || wo.status === 'approved'
    ).length;
    
    // Average order value
    const avgOrderValue = total > 0 ? totalRevenue / total : 0;
    
    return {
      total,
      pendingCount,
      thisWeekCount,
      totalRevenue,
      statusCounts,
      highPriorityCount,
      avgOrderValue,
    };
  }, [workOrders]);

  const getStatusColor = (status: string): string => {
    const colors = {
      draft: '#d9d9d9',
      pending: '#faad14',
      approved: '#1890ff',
      in_progress: '#13c2c2',
      completed: '#52c41a',
      cancelled: '#f5222d',
    };
    return colors[status as keyof typeof colors] || '#d9d9d9';
  };

  const getChangePercentage = (current: number, previous: number): number => {
    if (previous === 0) return current > 0 ? 100 : 0;
    return ((current - previous) / previous) * 100;
  };

  return (
    <Row gutter={16} style={{ marginBottom: 24 }}>
      {/* Total Work Orders */}
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="총 작업지시서"
            value={stats.total}
            prefix={<FileTextOutlined style={{ color: '#1890ff' }} />}
            suffix="개"
          />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            전체 작업지시서 수
          </Text>
        </Card>
      </Col>

      {/* Pending Approval */}
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="승인 대기"
            value={stats.pendingCount}
            prefix={<ClockCircleOutlined style={{ color: '#faad14' }} />}
            suffix="개"
            valueStyle={{ color: stats.pendingCount > 0 ? '#faad14' : undefined }}
          />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            즉시 처리 필요
          </Text>
        </Card>
      </Col>

      {/* This Week's Orders */}
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="이번 주 작업"
            value={stats.thisWeekCount}
            prefix={<CalendarOutlined style={{ color: '#13c2c2' }} />}
            suffix="개"
            valueStyle={{ color: '#13c2c2' }}
          />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            최근 7일간 생성
          </Text>
        </Card>
      </Col>

      {/* Total Revenue */}
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="총 수익"
            value={stats.totalRevenue}
            prefix={<DollarOutlined style={{ color: '#52c41a' }} />}
            precision={0}
            valueStyle={{ color: '#52c41a' }}
          />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            완료된 작업 기준
          </Text>
        </Card>
      </Col>

      {/* Status Distribution */}
      <Col xs={24}>
        <Card title="상태별 분포" size="small">
          <Row gutter={8}>
            {Object.entries(stats.statusCounts).map(([status, count]) => {
              const statusLabels = {
                draft: '초안',
                pending: '승인 대기',
                approved: '승인됨',
                in_progress: '진행중',
                completed: '완료',
                cancelled: '취소됨',
              };

              return (
                <Col key={status} flex="1" style={{ minWidth: '120px' }}>
                  <div
                    style={{
                      padding: '12px',
                      backgroundColor: getStatusColor(status),
                      borderRadius: '6px',
                      textAlign: 'center',
                      color: status === 'draft' ? '#000' : '#fff',
                    }}
                  >
                    <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
                      {count}
                    </div>
                    <div style={{ fontSize: '12px', opacity: 0.9 }}>
                      {statusLabels[status as keyof typeof statusLabels]}
                    </div>
                  </div>
                </Col>
              );
            })}
          </Row>
        </Card>
      </Col>

      {/* Additional Metrics */}
      <Col xs={24}>
        <Row gutter={16}>
          {/* Average Order Value */}
          <Col xs={24} sm={8}>
            <Card size="small">
              <Statistic
                title="평균 주문 가치"
                value={stats.avgOrderValue}
                prefix="$"
                precision={0}
                valueStyle={{ fontSize: '16px' }}
              />
            </Card>
          </Col>

          {/* Completion Rate */}
          <Col xs={24} sm={8}>
            <Card size="small">
              <Statistic
                title="완료율"
                value={
                  stats.total > 0
                    ? ((stats.statusCounts.completed || 0) / stats.total) * 100
                    : 0
                }
                suffix="%"
                precision={1}
                valueStyle={{ fontSize: '16px', color: '#52c41a' }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>

          {/* Active Orders */}
          <Col xs={24} sm={8}>
            <Card size="small">
              <Statistic
                title="진행 중인 작업"
                value={
                  (stats.statusCounts.approved || 0) + 
                  (stats.statusCounts.in_progress || 0)
                }
                suffix="개"
                valueStyle={{ fontSize: '16px', color: '#1890ff' }}
                prefix={<ExclamationCircleOutlined />}
              />
            </Card>
          </Col>
        </Row>
      </Col>
    </Row>
  );
};

export default WorkOrderStats;