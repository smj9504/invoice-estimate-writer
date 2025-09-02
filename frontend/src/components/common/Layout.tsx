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
        label: 'Dashboard',
      },
      {
        key: '/documents',
        icon: <FileTextOutlined />,
        label: 'Documents',
        children: [
          {
            key: '/documents/estimate',
            label: 'Estimates',
          },
          {
            key: '/documents/invoice',
            label: 'Invoices',
          },
          {
            key: '/documents/insurance_estimate',
            label: 'Insurance Estimates',
          },
        ],
      },
      {
        key: '/work-orders',
        icon: <ProjectOutlined />,
        label: 'Work Orders',
      },
      {
        key: '/create',
        icon: <PlusOutlined />,
        label: 'Create Documents',
        children: [
          {
            key: '/create/estimate',
            label: 'Create Estimate',
          },
          {
            key: '/create/invoice',
            label: 'Create Invoice',
          },
          {
            key: '/create/insurance',
            label: 'Create Insurance Estimate',
          },
          {
            key: '/create/plumber',
            label: 'Create Plumber Report',
          },
          {
            key: '/create/work-order',
            label: 'Create Work Order',
          },
        ],
      },
    ];

    // Add admin menus only for admin users
    if (isAdmin()) {
      items.push({
        key: '/admin',
        icon: <SettingOutlined />,
        label: 'Admin',
        children: [
          {
            key: '/admin/dashboard',
            label: 'Admin Dashboard',
          },
          {
            key: '/admin/database',
            label: 'Database Management',
          },
          {
            key: '/admin/document-types',
            label: 'Document Type Management',
          },
          {
            key: '/admin/trades',
            label: 'Trade Management',
          },
          {
            key: '/admin/config',
            label: 'System Configuration',
          },
          {
            key: '/admin/users',
            label: 'User Management',
          },
          {
            key: '/companies',
            label: 'Company Management',
          },
        ],
      });
    } else if (isManager()) {
      // Managers can manage companies but not system settings
      items.push({
        key: '/companies',
        icon: <TeamOutlined />,
        label: 'Company Management',
      });
    }

    return items;
  }, [isAdmin, isManager]);

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: 'Settings',
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
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
                <span>Current Company:</span>
                <strong>{selectedCompany.name}</strong>
              </Space>
            )}
          </div>
          <Dropdown menu={{ items: userMenuItems, onClick: handleMenuClick }} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} />
              <span>{user?.full_name || user?.username || 'User'}</span>
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