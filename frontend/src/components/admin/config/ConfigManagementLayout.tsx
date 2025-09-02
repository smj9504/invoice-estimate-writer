/**
 * Configuration Management Layout Component
 * Main layout for all configuration modules with tabs
 */

import React, { useState } from 'react';
import { Card, Tabs, Alert, Space } from 'antd';
import {
  DollarOutlined,
  SettingOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import PaymentConfig from './PaymentConfig';

interface ConfigManagementLayoutProps {
  defaultTab?: string;
}

const ConfigManagementLayout: React.FC<ConfigManagementLayoutProps> = ({ 
  defaultTab = 'payment' 
}) => {
  const [activeTab, setActiveTab] = useState(defaultTab);

  const tabItems = [
    {
      key: 'payment',
      label: (
        <Space>
          <DollarOutlined />
          Payment
        </Space>
      ),
      children: (
        <>
          <Alert
            message="Payment Configuration"
            description="Manage payment methods and payment frequencies. These settings determine how companies can receive payments and payment schedules."
            type="info"
            showIcon
            icon={<InfoCircleOutlined />}
            style={{ marginBottom: 16 }}
          />
          <PaymentConfig />
        </>
      ),
    },
    // Future configuration tabs can be added here
    // Examples:
    // - Document Types
    // - Tax Rates
    // - Trade Categories
    // - Notification Templates
    // - System Settings
  ];

  return (
    <Card
      title={
        <Space>
          <SettingOutlined />
          <span>System Configuration</span>
        </Space>
      }
      style={{ height: '100%' }}
    >
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        type="card"
      />
    </Card>
  );
};

export default ConfigManagementLayout;