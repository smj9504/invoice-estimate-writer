import React, { useState } from 'react';
import {
  Table,
  Button,
  Space,
  Input,
  Row,
  Col,
  Card,
  Avatar,
  Modal,
  message,
  Tooltip,
  Tag,
} from 'antd';
import {
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  PlusOutlined,
  ExclamationCircleOutlined,
  PhoneOutlined,
  MailOutlined,
  EnvironmentOutlined,
  BuildOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { Company, CompanyFilter } from '../../types';

const { Search } = Input;
const { confirm } = Modal;

interface CompanyTableProps {
  companies: Company[];
  loading?: boolean;
  onEdit: (company: Company) => void;
  onDelete: (id: string) => Promise<void>;
  onAdd: () => void;
  filter: CompanyFilter;
  onFilterChange: (filter: CompanyFilter) => void;
}

const CompanyTable: React.FC<CompanyTableProps> = ({
  companies,
  loading = false,
  onEdit,
  onDelete,
  onAdd,
  filter,
  onFilterChange,
}) => {
  const [deleteLoading, setDeleteLoading] = useState<string | null>(null);

  const handleDelete = (company: Company) => {
    confirm({
      title: '회사 삭제',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p>정말로 <strong>{company.name}</strong>을(를) 삭제하시겠습니까?</p>
          <p style={{ color: '#ff4d4f', fontSize: '12px' }}>
            ⚠️ 이 작업은 되돌릴 수 없습니다.
          </p>
        </div>
      ),
      okText: '삭제',
      okType: 'danger',
      cancelText: '취소',
      onOk: async () => {
        setDeleteLoading(company.id);
        try {
          await onDelete(company.id);
          // 메시지는 상위 컴포넌트에서 처리
        } catch (error) {
          // 에러 메시지도 상위 컴포넌트에서 처리
        } finally {
          setDeleteLoading(null);
        }
      },
    });
  };

  const renderLogo = (logo?: string, name?: string) => {
    if (logo) {
      try {
        // Handle both base64 data URLs and regular URLs
        const logoSrc = logo.startsWith('data:image') ? logo : `data:image/png;base64,${logo}`;
        return (
          <Avatar
            src={logoSrc}
            size={40}
            alt={name}
            style={{ flexShrink: 0 }}
          />
        );
      } catch {
        return (
          <Avatar
            icon={<BuildOutlined />}
            size={40}
            style={{ backgroundColor: '#f0f0f0', color: '#999' }}
          />
        );
      }
    }
    return (
      <Avatar
        icon={<BuildOutlined />}
        size={40}
        style={{ backgroundColor: '#f0f0f0', color: '#999' }}
      />
    );
  };

  const columns: ColumnsType<Company> = [
    {
      title: '로고',
      dataIndex: 'logo',
      key: 'logo',
      width: 80,
      render: (logo, record) => renderLogo(logo, record.name),
    },
    {
      title: '회사명',
      dataIndex: 'name',
      key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
      render: (name, record) => (
        <div>
          <div style={{ fontWeight: 'bold', fontSize: '14px' }}>{name}</div>
          {record.email && (
            <div style={{ fontSize: '12px', color: '#666' }}>
              <MailOutlined style={{ marginRight: 4 }} />
              {record.email}
            </div>
          )}
        </div>
      ),
    },
    {
      title: '연락처',
      dataIndex: 'phone',
      key: 'phone',
      width: 150,
      render: (phone) => phone ? (
        <Tag icon={<PhoneOutlined />} color="blue">
          {phone}
        </Tag>
      ) : (
        <span style={{ color: '#ccc' }}>-</span>
      ),
    },
    {
      title: '주소',
      dataIndex: 'address',
      key: 'address',
      render: (address, record) => (
        <div>
          <div style={{ marginBottom: 4 }}>
            <EnvironmentOutlined style={{ marginRight: 4, color: '#666' }} />
            {address}
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {record.city}, {record.state} {record.zip}
          </div>
        </div>
      ),
    },
    {
      title: '작업',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="수정">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => onEdit(record)}
              size="small"
            />
          </Tooltip>
          <Tooltip title="삭제">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record)}
              loading={deleteLoading === record.id}
              size="small"
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  const filteredCompanies = companies.filter((company) => {
    const searchTerm = filter.search?.toLowerCase() || '';
    const cityFilter = filter.city?.toLowerCase() || '';
    const stateFilter = filter.state?.toLowerCase() || '';

    const matchesSearch = !searchTerm || 
      company.name.toLowerCase().includes(searchTerm) ||
      company.address?.toLowerCase().includes(searchTerm) ||
      company.email?.toLowerCase().includes(searchTerm) ||
      company.phone?.toLowerCase().includes(searchTerm);

    const matchesCity = !cityFilter || 
      company.city.toLowerCase().includes(cityFilter);

    const matchesState = !stateFilter || 
      company.state.toLowerCase().includes(stateFilter);

    return matchesSearch && matchesCity && matchesState;
  });

  return (
    <Card
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>등록된 회사 목록</span>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={onAdd}
          >
            새 회사 등록
          </Button>
        </div>
      }
      style={{ marginBottom: 24 }}
    >
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24}>
          <Search
            placeholder="회사명, 주소, 이메일, 전화번호 검색"
            value={filter.search}
            onChange={(e) => onFilterChange({ ...filter, search: e.target.value })}
            onSearch={(value) => onFilterChange({ ...filter, search: value })}
            enterButton={<SearchOutlined />}
            allowClear
            style={{ maxWidth: 500 }}
          />
        </Col>
      </Row>

      <Table
        columns={columns}
        dataSource={filteredCompanies}
        rowKey="id"
        loading={loading}
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) =>
            `${range[0]}-${range[1]} / 총 ${total}개`,
        }}
        scroll={{ x: 800 }}
        size="middle"
      />
    </Card>
  );
};

export default CompanyTable;