import React, { useMemo } from 'react';
import { Layout as AntLayout, Menu, Avatar, Dropdown, Space } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  FileTextOutlined,
  TeamOutlined,
  PlusOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  ProjectOutlined,
  BarChartOutlined,
  ToolOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';
import { useStore } from '../../store/useStore';
import { useAuth } from '../../contexts/AuthContext';

const { Header, Sider, Content } = AntLayout;

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { selectedCompany } = useStore();
  const { user, logout, isAdmin, isManager } = useAuth();

  const menuItems = useMemo(() => {
    const items = [
      {
        key: '/dashboard',
        icon: <DashboardOutlined />,
        label: '대시보드',
      },
      {
        key: '/documents',
        icon: <FileTextOutlined />,
        label: '서류 목록',
        children: [
          {
            key: '/documents/estimate',
            label: '견적서',
          },
          {
            key: '/documents/invoice',
            label: '인보이스',
          },
          {
            key: '/documents/insurance_estimate',
            label: '보험 견적서',
          },
        ],
      },
      {
        key: '/work-orders',
        icon: <ProjectOutlined />,
        label: '작업 지시서',
      },
      {
        key: '/create',
        icon: <PlusOutlined />,
        label: '서류 작성',
        children: [
          {
            key: '/create/estimate',
            label: '견적서 작성',
          },
          {
            key: '/create/invoice',
            label: '인보이스 작성',
          },
          {
            key: '/create/insurance',
            label: '보험 견적서 작성',
          },
          {
            key: '/create/plumber',
            label: '배관공 보고서 작성',
          },
          {
            key: '/create/work-order',
            label: '작업 지시서 작성',
          },
        ],
      },
    ];

    // Add admin menus only for admin users
    if (isAdmin()) {
      items.push({
        key: '/admin',
        icon: <SettingOutlined />,
        label: '관리자',
        children: [
          {
            key: '/admin/dashboard',
            label: '관리자 대시보드',
          },
          {
            key: '/admin/database',
            label: '데이터베이스 관리',
          },
          {
            key: '/admin/document-types',
            label: '문서 유형 관리',
          },
          {
            key: '/admin/trades',
            label: '업종 관리',
          },
          {
            key: '/admin/users',
            label: '사용자 관리',
          },
          {
            key: '/companies',
            label: '회사 관리',
          },
        ],
      });
    } else if (isManager()) {
      // Managers can manage companies but not system settings
      items.push({
        key: '/companies',
        icon: <TeamOutlined />,
        label: '회사 관리',
      });
    }

    return items;
  }, [isAdmin, isManager]);

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '프로필',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '설정',
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '로그아웃',
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    if (key === 'logout') {
      logout();
      navigate('/login');
    } else if (key === 'profile') {
      navigate('/profile');
    } else if (key === 'settings') {
      navigate('/settings');
    } else {
      navigate(key);
    }
  };

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider
        breakpoint="lg"
        collapsedWidth="0"
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div style={{ 
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: 'white',
          fontSize: '20px',
          fontWeight: 'bold',
        }}>
          MJ Estimate
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <AntLayout style={{ marginLeft: 200 }}>
        <Header style={{ 
          padding: '0 24px', 
          background: '#fff',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 1px 4px rgba(0,21,41,.08)',
        }}>
          <div>
            {selectedCompany && (
              <Space>
                <span>현재 회사:</span>
                <strong>{selectedCompany.name}</strong>
              </Space>
            )}
          </div>
          <Dropdown menu={{ items: userMenuItems, onClick: handleMenuClick }} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} />
              <span>{user?.full_name || user?.username || '사용자'}</span>
            </Space>
          </Dropdown>
        </Header>
        <Content style={{ margin: '24px', minHeight: 280 }}>
          {children}
        </Content>
      </AntLayout>
    </AntLayout>
  );
}

export default Layout;