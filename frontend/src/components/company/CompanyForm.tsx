import React, { useEffect } from 'react';
import {
  Form,
  Input,
  Button,
  Row,
  Col,
  Space,
} from 'antd';
import { SaveOutlined, CloseOutlined } from '@ant-design/icons';
import { Company, CompanyFormData } from '../../types';
import LogoUpload from './LogoUpload';

interface CompanyFormProps {
  initialData?: Company;
  onSubmit: (data: CompanyFormData) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

const CompanyForm: React.FC<CompanyFormProps> = ({
  initialData,
  onSubmit,
  onCancel,
  loading = false,
}) => {
  const [form] = Form.useForm();

  useEffect(() => {
    if (initialData) {
      form.setFieldsValue({
        name: initialData.name,
        address: initialData.address,
        city: initialData.city,
        state: initialData.state,
        zipcode: initialData.zipcode,
        phone: initialData.phone,
        email: initialData.email,
        logo: initialData.logo,
      });
    } else {
      form.resetFields();
    }
  }, [initialData, form]);

  const handleSubmit = async (values: CompanyFormData) => {
    try {
      await onSubmit(values);
      if (!initialData) {
        form.resetFields();
      }
      // 메시지는 상위 컴포넌트에서 처리
    } catch (error) {
      // 에러 메시지도 상위 컴포넌트에서 처리
    }
  };

  const validateMessages = {
    required: '${label}을(를) 입력해주세요.', // eslint-disable-line no-template-curly-in-string
    types: {
      email: '올바른 이메일 형식이 아닙니다.',
    },
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      validateMessages={validateMessages}
      initialValues={{
        name: '',
        address: '',
        city: '',
        state: '',
        zipcode: '',
        phone: '',
        email: '',
        logo: '',
      }}
    >
      <Row gutter={[24, 0]}>
        <Col xs={24}>
          <h3>{initialData ? '회사 정보 수정' : '새 회사 등록'}</h3>
        </Col>
      </Row>

      <Row gutter={[24, 0]}>
        <Col xs={24}>
          <Form.Item
            name="logo"
            label="회사 로고"
          >
            <LogoUpload disabled={loading} />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={[16, 0]}>
        <Col xs={24} md={12}>
          <Form.Item
            name="name"
            label="회사명"
            rules={[{ required: true }]}
          >
            <Input
              placeholder="회사명을 입력하세요"
              disabled={loading}
            />
          </Form.Item>
        </Col>
        <Col xs={24} md={12}>
          <Form.Item
            name="phone"
            label="전화번호"
          >
            <Input
              placeholder="전화번호를 입력하세요"
              disabled={loading}
            />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={[16, 0]}>
        <Col xs={24} md={12}>
          <Form.Item
            name="email"
            label="이메일"
            rules={[{ type: 'email' }]}
          >
            <Input
              placeholder="이메일을 입력하세요"
              disabled={loading}
            />
          </Form.Item>
        </Col>
        <Col xs={24} md={12}>
          <Form.Item
            name="zipcode"
            label="우편번호"
          >
            <Input
              placeholder="우편번호를 입력하세요"
              disabled={loading}
            />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={[16, 0]}>
        <Col xs={24}>
          <Form.Item
            name="address"
            label="주소"
            rules={[{ required: true }]}
          >
            <Input
              placeholder="주소를 입력하세요"
              disabled={loading}
            />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={[16, 0]}>
        <Col xs={24} md={12}>
          <Form.Item
            name="city"
            label="도시"
            rules={[{ required: true }]}
          >
            <Input
              placeholder="도시를 입력하세요"
              disabled={loading}
            />
          </Form.Item>
        </Col>
        <Col xs={24} md={12}>
          <Form.Item
            name="state"
            label="주/도"
            rules={[{ required: true }]}
          >
            <Input
              placeholder="주/도를 입력하세요"
              disabled={loading}
            />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24}>
          <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
            <Button
              onClick={onCancel}
              disabled={loading}
            >
              <CloseOutlined />
              취소
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              icon={<SaveOutlined />}
            >
              {initialData ? '수정' : '등록'}
            </Button>
          </Space>
        </Col>
      </Row>
    </Form>
  );
};

export default CompanyForm;