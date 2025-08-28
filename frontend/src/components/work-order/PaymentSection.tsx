import React, { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  Row,
  Col,
  Typography,
  Divider,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  DatePicker,
  message,
  Descriptions,
  Table,
  Popconfirm,
  Tooltip,
  Progress,
} from 'antd';
import {
  DollarOutlined,
  CreditCardOutlined,
  BankOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  FileTextOutlined,
  CalendarOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { WorkOrder } from '../../types';
import { workOrderService } from '../../services/workOrderService';
import type { ColumnsType } from 'antd/es/table';
import dayjs, { Dayjs } from 'dayjs';

const { Text, Title } = Typography;
const { TextArea } = Input;

interface PaymentRecord {
  id: string;
  amount: number;
  payment_method: 'cash' | 'check' | 'credit_card' | 'bank_transfer' | 'other';
  payment_date: string;
  reference_number?: string;
  notes?: string;
  status: 'pending' | 'completed' | 'failed' | 'refunded';
  created_at: string;
  created_by?: string;
}

interface PaymentSectionProps {
  workOrder: WorkOrder;
}

interface PaymentModalProps {
  visible: boolean;
  onCancel: () => void;
  workOrder: WorkOrder;
  editingPayment?: PaymentRecord | null;
}

const paymentMethodLabels = {
  cash: '현금',
  check: '수표',
  credit_card: '신용카드',
  bank_transfer: '계좌이체',
  other: '기타',
};

const paymentStatusConfig = {
  pending: { color: 'warning', label: '대기중', icon: <ClockCircleOutlined /> },
  completed: { color: 'success', label: '완료', icon: <CheckCircleOutlined /> },
  failed: { color: 'error', label: '실패', icon: <ExclamationCircleOutlined /> },
  refunded: { color: 'default', label: '환불됨', icon: <ExclamationCircleOutlined /> },
};

const PaymentModal: React.FC<PaymentModalProps> = ({
  visible,
  onCancel,
  workOrder,
  editingPayment,
}) => {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const paymentMutation = useMutation({
    mutationFn: (data: any) => 
      editingPayment 
        ? workOrderService.updatePayment(editingPayment.id, data)
        : workOrderService.addPayment(workOrder.id, data),
    onSuccess: () => {
      message.success(editingPayment ? '결제 정보가 수정되었습니다.' : '결제가 기록되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['work-order', workOrder.id] });
      queryClient.invalidateQueries({ queryKey: ['work-order-payments', workOrder.id] });
      form.resetFields();
      onCancel();
    },
    onError: (error: any) => {
      message.error(error.message || '결제 처리에 실패했습니다.');
    },
  });

  const handleSubmit = useCallback(() => {
    form.validateFields().then((values) => {
      const payload = {
        ...values,
        payment_date: values.payment_date?.format('YYYY-MM-DD') || dayjs().format('YYYY-MM-DD'),
      };
      paymentMutation.mutate(payload);
    });
  }, [form, paymentMutation]);

  React.useEffect(() => {
    if (editingPayment && visible) {
      form.setFieldsValue({
        ...editingPayment,
        payment_date: dayjs(editingPayment.payment_date),
      });
    } else if (visible) {
      form.resetFields();
      form.setFieldsValue({
        payment_date: dayjs(),
        payment_method: 'credit_card',
        status: 'completed',
      });
    }
  }, [editingPayment, visible, form]);

  const remainingAmount = workOrder.final_cost; // This would be calculated from existing payments

  return (
    <Modal
      title={editingPayment ? '결제 정보 수정' : '결제 기록 추가'}
      open={visible}
      onCancel={onCancel}
      onOk={handleSubmit}
      confirmLoading={paymentMutation.isPending}
      okText={editingPayment ? '수정' : '기록'}
      cancelText="취소"
      width={600}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          payment_date: dayjs(),
          payment_method: 'credit_card',
          status: 'completed',
        }}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="amount"
              label="결제 금액"
              rules={[
                { required: true, message: '결제 금액을 입력해주세요.' },
                { type: 'number', min: 0.01, message: '0보다 큰 금액을 입력해주세요.' },
              ]}
            >
              <InputNumber
                style={{ width: '100%' }}
                prefix="$"
                placeholder="0.00"
                precision={2}
                max={remainingAmount}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="payment_method"
              label="결제 방법"
              rules={[{ required: true, message: '결제 방법을 선택해주세요.' }]}
            >
              <Select placeholder="결제 방법 선택">
                {Object.entries(paymentMethodLabels).map(([value, label]) => (
                  <Select.Option key={value} value={value}>
                    {label}
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="payment_date"
              label="결제일"
              rules={[{ required: true, message: '결제일을 선택해주세요.' }]}
            >
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="status"
              label="결제 상태"
              rules={[{ required: true, message: '결제 상태를 선택해주세요.' }]}
            >
              <Select placeholder="상태 선택">
                {Object.entries(paymentStatusConfig).map(([value, config]) => (
                  <Select.Option key={value} value={value}>
                    <Space>
                      {config.icon}
                      {config.label}
                    </Space>
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          name="reference_number"
          label="참조 번호"
        >
          <Input placeholder="거래 번호, 수표 번호 등" />
        </Form.Item>

        <Form.Item
          name="notes"
          label="메모"
        >
          <TextArea
            rows={3}
            placeholder="결제에 대한 추가 정보나 메모를 입력하세요"
            maxLength={500}
            showCount
          />
        </Form.Item>
      </Form>

      {!editingPayment && (
        <div style={{ marginTop: 16, padding: 16, backgroundColor: '#f5f5f5', borderRadius: 6 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Text type="secondary">작업 총 비용:</Text>
              <br />
              <Text strong>${workOrder.final_cost.toLocaleString()}</Text>
            </Col>
            <Col span={8}>
              <Text type="secondary">기존 결제:</Text>
              <br />
              <Text strong>$0.00</Text> {/* This would be calculated */}
            </Col>
            <Col span={8}>
              <Text type="secondary">잔여 금액:</Text>
              <br />
              <Text strong style={{ color: '#fa541c' }}>
                ${remainingAmount.toLocaleString()}
              </Text>
            </Col>
          </Row>
        </div>
      )}
    </Modal>
  );
};

const PaymentSection: React.FC<PaymentSectionProps> = ({ workOrder }) => {
  const [paymentModalVisible, setPaymentModalVisible] = useState(false);
  const [editingPayment, setEditingPayment] = useState<PaymentRecord | null>(null);
  const queryClient = useQueryClient();

  // Mock payment data - in real app, this would come from an API
  const payments: PaymentRecord[] = [
    // This would be fetched from the backend
  ];

  const deletePaymentMutation = useMutation({
    mutationFn: workOrderService.deletePayment,
    onSuccess: () => {
      message.success('결제 기록이 삭제되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['work-order', workOrder.id] });
      queryClient.invalidateQueries({ queryKey: ['work-order-payments', workOrder.id] });
    },
    onError: (error: any) => {
      message.error(error.message || '삭제에 실패했습니다.');
    },
  });

  const handleEditPayment = useCallback((payment: PaymentRecord) => {
    setEditingPayment(payment);
    setPaymentModalVisible(true);
  }, []);

  const handleDeletePayment = useCallback((paymentId: string) => {
    deletePaymentMutation.mutate(paymentId);
  }, [deletePaymentMutation]);

  const totalPaid = payments
    .filter(p => p.status === 'completed')
    .reduce((sum, p) => sum + p.amount, 0);
  
  const remainingAmount = Math.max(0, workOrder.final_cost - totalPaid);
  const paymentProgress = workOrder.final_cost > 0 
    ? Math.round((totalPaid / workOrder.final_cost) * 100) 
    : 0;

  const paymentColumns: ColumnsType<PaymentRecord> = [
    {
      title: '결제일',
      dataIndex: 'payment_date',
      key: 'payment_date',
      render: (date: string) => new Date(date).toLocaleDateString('ko-KR'),
    },
    {
      title: '금액',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number) => `$${amount.toLocaleString()}`,
      align: 'right',
    },
    {
      title: '방법',
      dataIndex: 'payment_method',
      key: 'payment_method',
      render: (method: keyof typeof paymentMethodLabels) => paymentMethodLabels[method],
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      render: (status: keyof typeof paymentStatusConfig) => {
        const config = paymentStatusConfig[status];
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.label}
          </Tag>
        );
      },
    },
    {
      title: '참조 번호',
      dataIndex: 'reference_number',
      key: 'reference_number',
      render: (ref: string) => ref || '-',
    },
    {
      title: '작업',
      key: 'actions',
      render: (_, record: PaymentRecord) => (
        <Space>
          <Tooltip title="수정">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEditPayment(record)}
            />
          </Tooltip>
          <Popconfirm
            title="결제 기록 삭제"
            description="이 결제 기록을 삭제하시겠습니까?"
            onConfirm={() => handleDeletePayment(record.id)}
            okText="삭제"
            cancelText="취소"
          >
            <Tooltip title="삭제">
              <Button
                type="text"
                size="small"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <Card 
        title={
          <Space>
            <DollarOutlined />
            비용 및 결제 정보
          </Space>
        }
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            size="small"
            onClick={() => {
              setEditingPayment(null);
              setPaymentModalVisible(true);
            }}
            disabled={remainingAmount <= 0}
          >
            결제 기록
          </Button>
        }
        style={{ marginBottom: 24 }}
      >
        {/* Cost Breakdown */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col span={8}>
            <div style={{ textAlign: 'center', padding: '16px 0' }}>
              <DollarOutlined style={{ fontSize: 24, color: '#1890ff', marginBottom: 8 }} />
              <div>
                <Text type="secondary" style={{ fontSize: '12px' }}>기본 비용</Text>
                <div>
                  <Text strong style={{ fontSize: '18px' }}>
                    ${workOrder.base_cost.toLocaleString()}
                  </Text>
                </div>
              </div>
            </div>
          </Col>
          <Col span={8}>
            <div style={{ textAlign: 'center', padding: '16px 0' }}>
              <FileTextOutlined style={{ fontSize: 24, color: '#52c41a', marginBottom: 8 }} />
              <div>
                <Text type="secondary" style={{ fontSize: '12px' }}>적용된 크레딧</Text>
                <div>
                  <Text strong style={{ fontSize: '18px', color: '#52c41a' }}>
                    -${workOrder.credits_applied.toLocaleString()}
                  </Text>
                </div>
              </div>
            </div>
          </Col>
          <Col span={8}>
            <div style={{ textAlign: 'center', padding: '16px 0' }}>
              <CreditCardOutlined style={{ fontSize: 24, color: '#fa541c', marginBottom: 8 }} />
              <div>
                <Text type="secondary" style={{ fontSize: '12px' }}>최종 비용</Text>
                <div>
                  <Text strong style={{ fontSize: '20px', color: '#fa541c' }}>
                    ${workOrder.final_cost.toLocaleString()}
                  </Text>
                </div>
              </div>
            </div>
          </Col>
        </Row>

        <Divider />

        {/* Payment Progress */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <Text strong>결제 진행률</Text>
            <Text>{paymentProgress}%</Text>
          </div>
          <Progress
            percent={paymentProgress}
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
            status={paymentProgress === 100 ? 'success' : 'active'}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
            <Space>
              <Text type="secondary">완료 결제:</Text>
              <Text strong>${totalPaid.toLocaleString()}</Text>
            </Space>
            <Space>
              <Text type="secondary">잔여 금액:</Text>
              <Text strong style={{ color: remainingAmount > 0 ? '#fa541c' : '#52c41a' }}>
                ${remainingAmount.toLocaleString()}
              </Text>
            </Space>
          </div>
        </div>

        {/* Cost Override Note */}
        {workOrder.cost_override && workOrder.cost_override !== workOrder.final_cost && (
          <div style={{ marginBottom: 16, padding: 12, backgroundColor: '#fff2e8', borderRadius: 6, border: '1px solid #ffd591' }}>
            <Space>
              <ExclamationCircleOutlined style={{ color: '#fa541c' }} />
              <div>
                <Text strong>비용 재조정</Text>
                <br />
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  원래 계산된 비용에서 수동으로 조정되었습니다.
                </Text>
              </div>
            </Space>
          </div>
        )}

        {/* Payment History */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <Text strong>결제 내역</Text>
            <Tag color="blue">{payments.length}건</Tag>
          </div>
          
          {payments.length > 0 ? (
            <Table
              columns={paymentColumns}
              dataSource={payments}
              rowKey="id"
              size="small"
              pagination={false}
              style={{ marginTop: 16 }}
            />
          ) : (
            <div style={{ textAlign: 'center', padding: '40px 0', color: '#bfbfbf' }}>
              <CreditCardOutlined style={{ fontSize: 48, marginBottom: 16 }} />
              <div>아직 결제 기록이 없습니다</div>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                결제가 완료되면 여기에 기록됩니다
              </Text>
            </div>
          )}
        </div>
      </Card>

      <PaymentModal
        visible={paymentModalVisible}
        onCancel={() => {
          setPaymentModalVisible(false);
          setEditingPayment(null);
        }}
        workOrder={workOrder}
        editingPayment={editingPayment}
      />
    </>
  );
};

export default PaymentSection;