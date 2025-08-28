import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Form, Input, Button, Card, Typography, Space, Alert } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';

const { Title, Text, Link } = Typography;

const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const from = location.state?.from?.pathname || '/dashboard';

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    setError(null);
    
    try {
      await login(values.username, values.password);
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err.response?.data?.detail || '로그인에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleInitAdmin = async () => {
    try {
      const response = await fetch('/api/auth/init-admin', {
        method: 'POST',
      });
      const data = await response.json();
      if (response.ok) {
        setError(null);
        alert(data.message);
      } else {
        setError(data.detail || 'Failed to initialize admin');
      }
    } catch (err) {
      setError('Failed to initialize admin');
    }
  };

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      backgroundColor: '#f0f2f5'
    }}>
      <Card style={{ width: 400, boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <Title level={2}>MJ Estimate</Title>
            <Text type="secondary">계정에 로그인하세요</Text>
          </div>

          {error && (
            <Alert 
              message={error} 
              type="error" 
              closable 
              onClose={() => setError(null)} 
            />
          )}

          <Form
            name="login"
            onFinish={onFinish}
            autoComplete="off"
            layout="vertical"
            requiredMark={false}
          >
            <Form.Item
              name="username"
              rules={[{ required: true, message: '사용자명을 입력해주세요' }]}
            >
              <Input 
                size="large"
                prefix={<UserOutlined />} 
                placeholder="사용자명 또는 이메일" 
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: '비밀번호를 입력해주세요' }]}
            >
              <Input.Password 
                size="large"
                prefix={<LockOutlined />} 
                placeholder="비밀번호" 
              />
            </Form.Item>

            <Form.Item>
              <Button 
                type="primary" 
                htmlType="submit" 
                size="large"
                loading={loading} 
                block
              >
                로그인
              </Button>
            </Form.Item>
          </Form>

          <div style={{ textAlign: 'center' }}>
            <Space split="|">
              <Link onClick={() => navigate('/register')}>회원가입</Link>
              <Link onClick={() => navigate('/forgot-password')}>비밀번호 찾기</Link>
            </Space>
          </div>

          {/* Development only: Initialize admin button */}
          {process.env.NODE_ENV === 'development' && (
            <Alert
              message="개발 모드"
              description={
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text>초기 관리자 계정 생성 (최초 1회만 가능)</Text>
                  <Button size="small" onClick={handleInitAdmin}>
                    관리자 초기화
                  </Button>
                  <Text type="secondary">
                    Username: admin / Password: admin123
                  </Text>
                </Space>
              }
              type="info"
              showIcon
            />
          )}
        </Space>
      </Card>
    </div>
  );
};

export default Login;