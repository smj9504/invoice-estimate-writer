import React, { useState, useEffect } from 'react';
import { 
  Row, 
  Col, 
  Card, 
  Button, 
  Space, 
  Typography, 
  DatePicker, 
  Select, 
  Switch,
  message,
  Modal,
  Table,
  Alert,
  Badge,
  Dropdown,
  Divider,
  Progress,
  List,
  Avatar,
  Statistic,
  Tag,
  Tooltip
} from 'antd';
import {
  ReloadOutlined,
  DownloadOutlined,
  SettingOutlined,
  PlusOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  DollarOutlined,
  FileTextOutlined,
  TeamOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  AlertOutlined,
  EyeOutlined,
  FilterOutlined,
  AppstoreOutlined,
  ToolOutlined,
  UserOutlined
} from '@ant-design/icons';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import dayjs, { Dayjs } from 'dayjs';

// Custom components
import MetricCard from '../components/dashboard/MetricCard';
import RevenueChart from '../components/dashboard/RevenueChart';
import StatusDistributionChart from '../components/dashboard/StatusDistributionChart';
import RecentActivityFeed from '../components/dashboard/RecentActivityFeed';

// Services
import { 
  dashboardService, 
  DashboardData,
  DashboardFilters 
} from '../services/dashboardService';
import { workOrderService } from '../services/workOrderService';
import { companyService } from '../services/companyService';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  // State management
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs().subtract(30, 'days'),
    dayjs()
  ]);
  const [selectedCompany, setSelectedCompany] = useState<string>('');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(30); // seconds
  const [selectedWorkOrders, setSelectedWorkOrders] = useState<string[]>([]);
  const [alertsVisible, setAlertsVisible] = useState(true);

  // Build filters for API calls
  const filters: DashboardFilters = {
    date_from: dateRange[0].format('YYYY-MM-DD'),
    date_to: dateRange[1].format('YYYY-MM-DD'),
    ...(selectedCompany && { company_id: selectedCompany }),
    refresh: autoRefresh
  };

  // Data fetching with React Query
  const { 
    data: dashboardData, 
    isLoading: dashboardLoading, 
    isError: dashboardError,
    refetch: refetchDashboard 
  } = useQuery({
    queryKey: ['dashboard', filters],
    queryFn: () => dashboardService.getMockDashboardData(), // Switch to real API when ready
    refetchInterval: autoRefresh ? refreshInterval * 1000 : false,
    staleTime: 60 * 1000, // 1 minute
  });

  const { data: companies } = useQuery({
    queryKey: ['companies'],
    queryFn: () => companyService.getCompanies(),
  });

  const { data: pendingWorkOrders } = useQuery({
    queryKey: ['work-orders', 'pending'],
    queryFn: () => workOrderService.searchWorkOrders({ 
      status: 'pending' as any,
      page_size: 50
    }),
  });

  // Auto-refresh effect
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        refetchDashboard();
      }, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, refetchDashboard]);

  // Event handlers
  const handleRefresh = async () => {
    try {
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      message.success('대시보드가 새로고침되었습니다');
    } catch (error) {
      message.error('새로고침 중 오류가 발생했습니다');
    }
  };

  const handleExport = async (type: 'excel' | 'pdf') => {
    try {
      const blob = await dashboardService.exportReport(type, filters);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `dashboard-report-${dayjs().format('YYYY-MM-DD')}.${type}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      message.success(`${type.toUpperCase()} 파일이 다운로드되었습니다`);
    } catch (error) {
      message.error('내보내기 중 오류가 발생했습니다');
    }
  };

  const handleBulkApprove = async () => {
    if (selectedWorkOrders.length === 0) {
      message.warning('승인할 작업 지시서를 선택해주세요');
      return;
    }

    Modal.confirm({
      title: '일괄 승인',
      content: `선택한 ${selectedWorkOrders.length}개의 작업 지시서를 승인하시겠습니까?`,
      onOk: async () => {
        try {
          await dashboardService.approveMultipleOrders(selectedWorkOrders);
          message.success('작업 지시서가 일괄 승인되었습니다');
          setSelectedWorkOrders([]);
          refetchDashboard();
        } catch (error) {
          message.error('일괄 승인 중 오류가 발생했습니다');
        }
      }
    });
  };

  const stats = dashboardData?.stats;

  if (dashboardError) {
    return (
      <div>
        <Alert
          message="데이터 로딩 오류"
          description="대시보드 데이터를 불러오는 중 오류가 발생했습니다. 새로고침을 시도해주세요."
          type="error"
          action={
            <Button size="small" danger onClick={handleRefresh}>
              새로고침
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div style={{ padding: '0 24px 24px 0' }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: 24,
        padding: '16px 0'
      }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>
            관리자 대시보드
          </Title>
          <Text type="secondary">
            작업 지시서 시스템 현황 및 분석
          </Text>
        </div>

        <Space size="middle">
          {/* Date Range Picker */}
          <RangePicker
            value={dateRange}
            onChange={(dates) => dates && setDateRange(dates as [Dayjs, Dayjs])}
            format="YYYY-MM-DD"
            style={{ width: 240 }}
          />

          {/* Company Filter */}
          <Select
            placeholder="회사 선택"
            style={{ width: 200 }}
            value={selectedCompany}
            onChange={setSelectedCompany}
            allowClear
            showSearch
            options={companies?.map(company => ({
              label: company.name,
              value: company.id
            }))}
          />

          {/* Auto Refresh */}
          <Space>
            <Text>자동 새로고침:</Text>
            <Switch
              checked={autoRefresh}
              onChange={setAutoRefresh}
              checkedChildren="ON"
              unCheckedChildren="OFF"
            />
          </Space>

          {/* Action Buttons */}
          <Space>
            <Button 
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              loading={dashboardLoading}
            >
              새로고침
            </Button>

            <Dropdown
              menu={{
                items: [
                  {
                    key: 'excel',
                    label: 'Excel 내보내기',
                    icon: <DownloadOutlined />,
                    onClick: () => handleExport('excel')
                  },
                  {
                    key: 'pdf',
                    label: 'PDF 내보내기',
                    icon: <DownloadOutlined />,
                    onClick: () => handleExport('pdf')
                  }
                ]
              }}
            >
              <Button icon={<DownloadOutlined />}>
                내보내기
              </Button>
            </Dropdown>

            <Button 
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => navigate('/work-orders/new')}
            >
              작업 지시서 생성
            </Button>
          </Space>
        </Space>
      </div>

      {/* Alerts Section */}
      {alertsVisible && dashboardData?.alerts && dashboardData.alerts.length > 0 && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={24}>
            <Card>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <AlertOutlined style={{ color: '#fa8c16', marginRight: 8 }} />
                  <Title level={4} style={{ margin: 0 }}>
                    알림 및 경고
                  </Title>
                  <Badge count={dashboardData.alerts.length} style={{ marginLeft: 12 }} />
                </div>
                <Button 
                  type="text" 
                  size="small"
                  onClick={() => setAlertsVisible(false)}
                >
                  닫기
                </Button>
              </div>

              <List
                dataSource={dashboardData.alerts.slice(0, 3)}
                renderItem={alert => (
                  <List.Item>
                    <List.Item.Meta
                      avatar={
                        <Avatar 
                          icon={<AlertOutlined />}
                          style={{ 
                            backgroundColor: alert.severity === 'critical' ? '#ff4d4f' : 
                                            alert.severity === 'high' ? '#fa8c16' :
                                            alert.severity === 'medium' ? '#faad14' : '#d9d9d9'
                          }}
                        />
                      }
                      title={
                        <Space>
                          {alert.title}
                          <Tag 
                            color={
                              alert.severity === 'critical' ? 'red' : 
                              alert.severity === 'high' ? 'orange' :
                              alert.severity === 'medium' ? 'yellow' : 'default'
                            }
                          >
                            {alert.severity.toUpperCase()}
                          </Tag>
                        </Space>
                      }
                      description={alert.description}
                    />
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {dayjs(alert.timestamp).fromNow()}
                    </Text>
                  </List.Item>
                )}
              />
              
              {dashboardData.alerts.length > 3 && (
                <div style={{ textAlign: 'center', marginTop: 16 }}>
                  <Button type="link" size="small">
                    모든 알림 보기 ({dashboardData.alerts.length - 3}개 더)
                  </Button>
                </div>
              )}
            </Card>
          </Col>
        </Row>
      )}

      {/* Quick Links Section */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card 
            title={
              <Space>
                <SettingOutlined />
                <span>빠른 관리 메뉴</span>
              </Space>
            }
            size="small"
          >
            <Space wrap size="middle">
              <Button 
                type="primary" 
                icon={<FileTextOutlined />}
                onClick={() => navigate('/admin/document-types')}
              >
                문서 유형 관리
              </Button>
              <Button 
                type="primary" 
                icon={<ToolOutlined />}
                onClick={() => navigate('/admin/trades')}
              >
                업종 관리
              </Button>
              <Button 
                icon={<TeamOutlined />}
                onClick={() => navigate('/companies')}
              >
                회사 관리
              </Button>
              <Button 
                icon={<UserOutlined />}
                onClick={() => navigate('/staff')}
              >
                직원 관리
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Key Metrics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="전체 작업 지시서"
            value={stats?.total_work_orders || 0}
            prefix={<FileTextOutlined />}
            color="#1890ff"
            loading={dashboardLoading}
            onClick={() => navigate('/work-orders')}
            tooltip="시스템에 등록된 총 작업 지시서 수"
          />
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="이달 매출"
            value={stats?.revenue_this_month || 0}
            prefix="$"
            precision={0}
            color="#52c41a"
            loading={dashboardLoading}
            trend={{
              value: stats?.revenue_trend || 0,
              label: "지난달 대비"
            }}
            formatter={(value) => `$${Number(value).toLocaleString()}`}
            tooltip="현재 월의 총 매출액"
          />
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="승인 대기"
            value={stats?.pending_approvals || 0}
            prefix={<ClockCircleOutlined />}
            color="#fa8c16"
            loading={dashboardLoading}
            onClick={() => navigate('/work-orders?status=pending')}
            tooltip="승인이 필요한 작업 지시서 수"
          />
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <MetricCard
            title="진행 중"
            value={stats?.active_work_orders || 0}
            prefix={<CheckCircleOutlined />}
            color="#722ed1"
            loading={dashboardLoading}
            onClick={() => navigate('/work-orders?status=in_progress')}
            tooltip="현재 진행 중인 작업 지시서 수"
          />
        </Col>
      </Row>

      {/* Secondary Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={8}>
          <MetricCard
            title="완료율"
            value={stats?.completion_rate || 0}
            suffix="%"
            precision={1}
            color="#52c41a"
            loading={dashboardLoading}
            progress={{
              percent: stats?.completion_rate || 0,
              status: (stats?.completion_rate || 0) >= 80 ? 'success' : 'normal'
            }}
            tooltip="전체 작업 지시서 중 완료된 비율"
          />
        </Col>

        <Col xs={24} sm={12} lg={8}>
          <MetricCard
            title="평균 처리 시간"
            value={stats?.average_processing_time || 0}
            suffix="일"
            precision={1}
            color="#1890ff"
            loading={dashboardLoading}
            tooltip="작업 지시서 생성부터 완료까지의 평균 소요 시간"
          />
        </Col>

        <Col xs={24} sm={12} lg={8}>
          <MetricCard
            title="크레딧 사용률"
            value={dashboardData?.credit_usage?.utilization_rate || 0}
            suffix="%"
            precision={1}
            color="#722ed1"
            loading={dashboardLoading}
            progress={{
              percent: dashboardData?.credit_usage?.utilization_rate || 0,
              status: (dashboardData?.credit_usage?.utilization_rate || 0) >= 90 ? 'exception' : 'normal'
            }}
            tooltip="발급된 크레딧 대비 사용 비율"
          />
        </Col>
      </Row>

      {/* Charts Section */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={16}>
          <RevenueChart
            data={dashboardData?.revenue_chart || []}
            loading={dashboardLoading}
            height={400}
            showComparison
          />
        </Col>

        <Col xs={24} lg={8}>
          <StatusDistributionChart
            data={dashboardData?.status_distribution || []}
            loading={dashboardLoading}
            height={400}
          />
        </Col>
      </Row>

      {/* Document Type Distribution & Trade Popularity */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card 
            title="문서 유형별 분포"
            loading={dashboardLoading}
            extra={<Button type="link" size="small">더 보기</Button>}
          >
            <div style={{ height: 300 }}>
              {dashboardData?.document_type_distribution?.map((item, index) => (
                <div 
                  key={index}
                  style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    padding: '12px 0',
                    borderBottom: index < dashboardData.document_type_distribution.length - 1 ? '1px solid #f0f0f0' : 'none'
                  }}
                >
                  <div>
                    <Text strong>{item.document_type}</Text>
                    <br />
                    <Text type="secondary">{item.count}건</Text>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <Text strong>${item.revenue.toLocaleString()}</Text>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card 
            title="인기 업종"
            loading={dashboardLoading}
            extra={<Button type="link" size="small">더 보기</Button>}
          >
            <div style={{ height: 300 }}>
              {dashboardData?.trade_popularity?.map((item, index) => (
                <div 
                  key={index}
                  style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    padding: '12px 0',
                    borderBottom: index < dashboardData.trade_popularity.length - 1 ? '1px solid #f0f0f0' : 'none'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center' }}>
                    <Badge 
                      count={index + 1} 
                      style={{ 
                        backgroundColor: index === 0 ? '#faad14' : index === 1 ? '#d9d9d9' : index === 2 ? '#d48806' : '#f0f0f0',
                        color: index < 3 ? '#fff' : '#666'
                      }} 
                    />
                    <div style={{ marginLeft: 12 }}>
                      <Text strong>{item.trade_name}</Text>
                      <br />
                      <Text type="secondary">{item.count}건</Text>
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <Text strong>${item.revenue.toLocaleString()}</Text>
                    <br />
                    <Tag color={item.trend === 'up' ? 'green' : item.trend === 'down' ? 'red' : 'blue'}>
                      {item.trend === 'up' ? '상승' : item.trend === 'down' ? '하락' : '안정'}
                    </Tag>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </Col>
      </Row>

      {/* Bottom Section: Activities, Performance, Quick Actions */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <RecentActivityFeed
            data={dashboardData?.recent_activities || []}
            loading={dashboardLoading}
            maxItems={8}
            onRefresh={handleRefresh}
            onItemClick={(activity) => {
              if (activity.work_order_number) {
                // Navigate to work order detail
                navigate(`/work-orders/${activity.work_order_number}`);
              }
            }}
          />
        </Col>

        <Col xs={24} lg={12}>
          <Row gutter={[16, 16]}>
            {/* Quick Actions */}
            <Col span={24}>
              <Card title="빠른 작업">
                <Row gutter={[16, 16]}>
                  <Col xs={12} sm={8}>
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      block
                      size="large"
                      onClick={() => navigate('/work-orders/new')}
                      style={{ height: 60, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}
                    >
                      새 작업 지시서
                    </Button>
                  </Col>

                  <Col xs={12} sm={8}>
                    <Button
                      type="default"
                      icon={<AppstoreOutlined />}
                      block
                      size="large"
                      onClick={handleBulkApprove}
                      style={{ height: 60, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}
                    >
                      일괄 승인
                    </Button>
                  </Col>

                  <Col xs={12} sm={8}>
                    <Button
                      type="default"
                      icon={<SettingOutlined />}
                      block
                      size="large"
                      onClick={() => navigate('/settings')}
                      style={{ height: 60, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}
                    >
                      시스템 설정
                    </Button>
                  </Col>
                </Row>
              </Card>
            </Col>

            {/* Top Performing Staff */}
            <Col span={24}>
              <Card 
                title={
                  <Space>
                    <TrophyOutlined style={{ color: '#faad14' }} />
                    우수 직원
                  </Space>
                }
                extra={<Button type="link" size="small">더 보기</Button>}
              >
                <List
                  dataSource={dashboardData?.staff_performance?.slice(0, 3) || []}
                  renderItem={(staff, index) => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={
                          <Badge 
                            count={index + 1}
                            style={{ 
                              backgroundColor: index === 0 ? '#faad14' : index === 1 ? '#d9d9d9' : '#d48806'
                            }}
                          >
                            <Avatar icon={<TeamOutlined />} />
                          </Badge>
                        }
                        title={staff.staff_name}
                        description={`완료: ${staff.completed_orders}건 • 매출: $${staff.revenue_generated.toLocaleString()}`}
                      />
                      <div>
                        <Tooltip title="평점">
                          <Text strong style={{ color: '#faad14' }}>
                            ★{staff.rating}
                          </Text>
                        </Tooltip>
                      </div>
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </Col>
      </Row>
    </div>
  );
};

export default AdminDashboard;