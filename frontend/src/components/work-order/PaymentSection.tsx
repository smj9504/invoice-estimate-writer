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
  cash: 'Cash',
  check: 'Check',
  credit_card: 'Credit Card',
  bank_transfer: 'Bank Transfer',
  other: 'Other',
};

const paymentStatusConfig = {
  pending: { color: 'warning', label: 'Pending', icon: <ClockCircleOutlined /> },
  completed: { color: 'success', label: 'Completed', icon: <CheckCircleOutlined /> },
  failed: { color: 'error', label: 'Failed', icon: <ExclamationCircleOutlined /> },
  refunded: { color: 'default', label: 'Refunded', icon: <ExclamationCircleOutlined /> },
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
      message.success(editingPayment ? 'Payment information has been updated.' : 'Payment has been recorded.');
      queryClient.invalidateQueries({ queryKey: ['work-order', workOrder.id] });
      queryClient.invalidateQueries({ queryKey: ['work-order-payments', workOrder.id] });
      form.resetFields();
      onCancel();
    },
    onError: (error: any) => {
      message.error(error.message || 'Failed to process payment.');
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

  const remainingAmount = workOrder.final_cost || 0; // This would be calculated from existing payments

  return (
    <Modal
      title={editingPayment ? 'Edit Payment Information' : 'Add Payment Record'}
      open={visible}
      onCancel={onCancel}
      onOk={handleSubmit}
      confirmLoading={paymentMutation.isPending}
      okText={editingPayment ? 'Update' : 'Record'}
      cancelText="Cancel"
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
              label="Payment Amount"
              rules={[
                { required: true, message: 'Please enter payment amount.' },
                { type: 'number', min: 0.01, message: 'Please enter an amount greater than 0.' },
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
              label="Payment Method"
              rules={[{ required: true, message: 'Please select payment method.' }]}
            >
              <Select placeholder="Select payment method">
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
              label="Payment Date"
              rules={[{ required: true, message: 'Please select payment date.' }]}
            >
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="status"
              label="Payment Status"
              rules={[{ required: true, message: 'Please select payment status.' }]}
            >
              <Select placeholder="Select status">
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
          label="Reference Number"
        >
          <Input placeholder="Transaction number, check number, etc." />
        </Form.Item>

        <Form.Item
          name="notes"
          label="Notes"
        >
          <TextArea
            rows={3}
            placeholder="Enter any additional information or notes about the payment"
            maxLength={500}
            showCount
          />
        </Form.Item>
      </Form>

      {!editingPayment && (
        <div style={{ marginTop: 16, padding: 16, backgroundColor: '#f5f5f5', borderRadius: 6 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Text type="secondary">Total Cost:</Text>
              <br />
              <Text strong>${(workOrder.final_cost || 0).toLocaleString()}</Text>
            </Col>
            <Col span={8}>
              <Text type="secondary">Existing Payments:</Text>
              <br />
              <Text strong>$0.00</Text> {/* This would be calculated */}
            </Col>
            <Col span={8}>
              <Text type="secondary">Remaining Amount:</Text>
              <br />
              <Text strong style={{ color: '#fa541c' }}>
                ${(remainingAmount || 0).toLocaleString()}
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
      message.success('Payment record has been deleted.');
      queryClient.invalidateQueries({ queryKey: ['work-order', workOrder.id] });
      queryClient.invalidateQueries({ queryKey: ['work-order-payments', workOrder.id] });
    },
    onError: (error: any) => {
      message.error(error.message || 'Failed to delete.');
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
  
  const finalCost = workOrder.final_cost || 0;
  const remainingAmount = Math.max(0, finalCost - totalPaid);
  const paymentProgress = finalCost > 0 
    ? Math.round((totalPaid / finalCost) * 100) 
    : 0;

  const paymentColumns: ColumnsType<PaymentRecord> = [
    {
      title: 'Payment Date',
      dataIndex: 'payment_date',
      key: 'payment_date',
      render: (date: string) => new Date(date).toLocaleDateString('en-US'),
    },
    {
      title: 'Amount',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number) => `$${amount.toLocaleString()}`,
      align: 'right',
    },
    {
      title: 'Method',
      dataIndex: 'payment_method',
      key: 'payment_method',
      render: (method: keyof typeof paymentMethodLabels) => paymentMethodLabels[method],
    },
    {
      title: 'Status',
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
      title: 'Reference Number',
      dataIndex: 'reference_number',
      key: 'reference_number',
      render: (ref: string) => ref || '-',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record: PaymentRecord) => (
        <Space>
          <Tooltip title="Edit">
            <Button
              type="text"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEditPayment(record)}
            />
          </Tooltip>
          <Popconfirm
            title="Delete Payment Record"
            description="Are you sure you want to delete this payment record?"
            onConfirm={() => handleDeletePayment(record.id)}
            okText="Delete"
            cancelText="Cancel"
          >
            <Tooltip title="Delete">
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
            Cost and Payment Information
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
            Record Payment
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
                <Text type="secondary" style={{ fontSize: '12px' }}>Base Cost</Text>
                <div>
                  <Text strong style={{ fontSize: '18px' }}>
                    ${(workOrder.base_cost || 0).toLocaleString()}
                  </Text>
                </div>
              </div>
            </div>
          </Col>
          <Col span={8}>
            <div style={{ textAlign: 'center', padding: '16px 0' }}>
              <FileTextOutlined style={{ fontSize: 24, color: '#52c41a', marginBottom: 8 }} />
              <div>
                <Text type="secondary" style={{ fontSize: '12px' }}>Credits Applied</Text>
                <div>
                  <Text strong style={{ fontSize: '18px', color: '#52c41a' }}>
                    -${(workOrder.credits_applied || 0).toLocaleString()}
                  </Text>
                </div>
              </div>
            </div>
          </Col>
          <Col span={8}>
            <div style={{ textAlign: 'center', padding: '16px 0' }}>
              <CreditCardOutlined style={{ fontSize: 24, color: '#fa541c', marginBottom: 8 }} />
              <div>
                <Text type="secondary" style={{ fontSize: '12px' }}>Final Cost</Text>
                <div>
                  <Text strong style={{ fontSize: '20px', color: '#fa541c' }}>
                    ${(workOrder.final_cost || 0).toLocaleString()}
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
            <Text strong>Payment Progress</Text>
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
              <Text type="secondary">Completed Payments:</Text>
              <Text strong>${totalPaid.toLocaleString()}</Text>
            </Space>
            <Space>
              <Text type="secondary">Remaining Amount:</Text>
              <Text strong style={{ color: remainingAmount > 0 ? '#fa541c' : '#52c41a' }}>
                ${(remainingAmount || 0).toLocaleString()}
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
                <Text strong>Cost Override</Text>
                <br />
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  The cost has been manually adjusted from the original calculation.
                </Text>
              </div>
            </Space>
          </div>
        )}

        {/* Payment History */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <Text strong>Payment History</Text>
            <Tag color="blue">{payments.length} records</Tag>
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
              <div>No payment records yet</div>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                Payment records will appear here when completed
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