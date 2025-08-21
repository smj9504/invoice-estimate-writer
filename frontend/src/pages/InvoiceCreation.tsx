import React, { useState, useEffect } from 'react';
import {
  Form,
  Input,
  Button,
  DatePicker,
  InputNumber,
  Select,
  Card,
  Row,
  Col,
  Space,
  Table,
  Modal,
  message,
  Divider,
  Switch,
  Typography,
  Tooltip,
  Popconfirm,
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  SaveOutlined,
  EyeOutlined,
  EditOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { useNavigate } from 'react-router-dom';
import { invoiceService } from '../services/invoiceService';
import { companyService } from '../services/companyService';
import { Company } from '../types';

const { Title } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface InvoiceItem {
  name: string;
  description?: string;
  quantity: number;
  unit: string;
  rate: number;
  amount?: number;
}

const InvoiceCreation: React.FC = () => {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [items, setItems] = useState<InvoiceItem[]>([]);
  const [showInsurance, setShowInsurance] = useState(false);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<Company | null>(null);
  const [itemModalVisible, setItemModalVisible] = useState(false);
  const [editingItem, setEditingItem] = useState<InvoiceItem | null>(null);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [itemForm] = Form.useForm();

  useEffect(() => {
    loadCompanies();
  }, []);
  // eslint-disable-next-line react-hooks/exhaustive-deps

  const loadCompanies = async () => {
    try {
      const data = await companyService.getCompanies();
      setCompanies(data);
      if (data.length > 0) {
        setSelectedCompany(data[0]);
        form.setFieldsValue({
          company_name: data[0].name,
          company_address: data[0].address,
          company_city: data[0].city,
          company_state: data[0].state,
          company_zip: data[0].zip,
          company_phone: data[0].phone,
          company_email: data[0].email,
        });
      }
    } catch (error) {
      console.error('Failed to load companies:', error);
    }
  };

  const handleCompanyChange = (companyId: string) => {
    const company = companies.find(c => c.id === companyId);
    if (company) {
      setSelectedCompany(company);
      form.setFieldsValue({
        company_name: company.name,
        company_address: company.address,
        company_city: company.city,
        company_state: company.state,
        company_zip: company.zip,
        company_phone: company.phone,
        company_email: company.email,
      });
    }
  };

  const handleAddItem = () => {
    itemForm.resetFields();
    setEditingItem(null);
    setEditingIndex(null);
    setItemModalVisible(true);
  };

  const handleEditItem = (item: InvoiceItem, index: number) => {
    setEditingItem(item);
    setEditingIndex(index);
    itemForm.setFieldsValue(item);
    setItemModalVisible(true);
  };

  const handleItemSubmit = () => {
    itemForm.validateFields().then(values => {
      const newItem: InvoiceItem = {
        ...values,
        amount: values.quantity * values.rate,
      };

      if (editingIndex !== null) {
        const updatedItems = [...items];
        updatedItems[editingIndex] = newItem;
        setItems(updatedItems);
      } else {
        setItems([...items, newItem]);
      }

      setItemModalVisible(false);
      itemForm.resetFields();
      setEditingItem(null);
      setEditingIndex(null);
    });
  };

  const handleDeleteItem = (index: number) => {
    const updatedItems = items.filter((_, i) => i !== index);
    setItems(updatedItems);
  };

  const calculateTotals = () => {
    const subtotal = items.reduce((sum, item) => sum + (item.quantity * item.rate), 0);
    const taxRate = form.getFieldValue('tax_rate') || 0;
    const discount = form.getFieldValue('discount') || 0;
    const shipping = form.getFieldValue('shipping') || 0;
    
    const taxAmount = (subtotal - discount) * (taxRate / 100);
    const total = subtotal - discount + taxAmount + shipping;

    return {
      subtotal,
      taxAmount,
      total,
    };
  };

  const handleSave = async (status: string = 'draft') => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      const totals = calculateTotals();
      const invoiceData = {
        ...values,
        date: values.date ? values.date.format('YYYY-MM-DD') : dayjs().format('YYYY-MM-DD'),
        due_date: values.due_date ? values.due_date.format('YYYY-MM-DD') : dayjs().add(30, 'days').format('YYYY-MM-DD'),
        status,
        company: {
          name: values.company_name,
          address: values.company_address,
          city: values.company_city,
          state: values.company_state,
          zip: values.company_zip,
          phone: values.company_phone,
          email: values.company_email,
          logo: selectedCompany?.logo,
        },
        client: {
          name: values.client_name,
          address: values.client_address,
          city: values.client_city,
          state: values.client_state,
          zip: values.client_zip,
          phone: values.client_phone,
          email: values.client_email,
        },
        insurance: showInsurance ? {
          company: values.insurance_company,
          policy_number: values.insurance_policy_number,
          claim_number: values.insurance_claim_number,
          deductible: values.insurance_deductible,
        } : null,
        items,
        subtotal: totals.subtotal,
        tax_rate: values.tax_rate || 0,
        tax_amount: totals.taxAmount,
        discount: values.discount || 0,
        shipping: values.shipping || 0,
        total: totals.total,
        paid_amount: values.paid_amount || 0,
        payment_terms: values.payment_terms,
        notes: values.notes,
      };

      const response = await invoiceService.createInvoice(invoiceData);
      message.success('Invoice saved successfully!');
      navigate(`/invoices/${response.id}`);
    } catch (error) {
      message.error('Failed to save invoice');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handlePreviewPDF = async () => {
    try {
      setLoading(true);
      const values = await form.validateFields();
      const totals = calculateTotals();

      const pdfData = {
        invoice_number: values.invoice_number || `INV-${dayjs().format('YYYYMMDDHHmmss')}`,
        date: values.date ? values.date.format('YYYY-MM-DD') : dayjs().format('YYYY-MM-DD'),
        due_date: values.due_date ? values.due_date.format('YYYY-MM-DD') : dayjs().add(30, 'days').format('YYYY-MM-DD'),
        company: {
          name: values.company_name,
          address: values.company_address,
          city: values.company_city,
          state: values.company_state,
          zip: values.company_zip,
          phone: values.company_phone,
          email: values.company_email,
          logo: selectedCompany?.logo,
        },
        client: {
          name: values.client_name,
          address: values.client_address,
          city: values.client_city,
          state: values.client_state,
          zip: values.client_zip,
          phone: values.client_phone,
          email: values.client_email,
        },
        insurance: showInsurance ? {
          company: values.insurance_company,
          policy_number: values.insurance_policy_number,
          claim_number: values.insurance_claim_number,
          deductible: values.insurance_deductible,
        } : null,
        items,
        subtotal: totals.subtotal,
        tax_rate: values.tax_rate || 0,
        tax_amount: totals.taxAmount,
        discount: values.discount || 0,
        shipping: values.shipping || 0,
        total: totals.total,
        paid_amount: values.paid_amount || 0,
        payment_terms: values.payment_terms,
        notes: values.notes,
      };

      const blob = await invoiceService.previewPDF(pdfData);
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank');
    } catch (error) {
      message.error('Failed to generate PDF preview');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: '#',
      key: 'index',
      width: 50,
      render: (_: any, __: any, index: number) => index + 1,
    },
    {
      title: 'Item',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: 'Qty',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
      align: 'center' as const,
    },
    {
      title: 'Unit',
      dataIndex: 'unit',
      key: 'unit',
      width: 80,
      align: 'center' as const,
    },
    {
      title: 'Rate',
      dataIndex: 'rate',
      key: 'rate',
      width: 100,
      align: 'right' as const,
      render: (value: number) => `$${value.toFixed(2)}`,
    },
    {
      title: 'Amount',
      key: 'amount',
      width: 120,
      align: 'right' as const,
      render: (_: any, record: InvoiceItem) => `$${(record.quantity * record.rate).toFixed(2)}`,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_: any, record: InvoiceItem, index: number) => (
        <Space>
          <Tooltip title="Edit">
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEditItem(record, index)}
            />
          </Tooltip>
          <Popconfirm
            title="Delete this item?"
            onConfirm={() => handleDeleteItem(index)}
          >
            <Button
              size="small"
              danger
              icon={<DeleteOutlined />}
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const totals = calculateTotals();

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>Create Invoice</Title>
      
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          invoice_number: `INV-${dayjs().format('YYYYMMDDHHmmss')}`,
          date: dayjs(),
          due_date: dayjs().add(30, 'days'),
          tax_rate: 0,
          discount: 0,
          shipping: 0,
          paid_amount: 0,
        }}
      >
        <Row gutter={24}>
          {/* Invoice Details */}
          <Col xs={24} lg={12}>
            <Card title="Invoice Details" style={{ marginBottom: 24 }}>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="invoice_number"
                    label="Invoice Number"
                    rules={[{ required: true }]}
                  >
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="status"
                    label="Status"
                    initialValue="draft"
                  >
                    <Select>
                      <Option value="draft">Draft</Option>
                      <Option value="sent">Sent</Option>
                      <Option value="paid">Paid</Option>
                      <Option value="overdue">Overdue</Option>
                      <Option value="cancelled">Cancelled</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="date"
                    label="Invoice Date"
                    rules={[{ required: true }]}
                  >
                    <DatePicker style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="due_date"
                    label="Due Date"
                    rules={[{ required: true }]}
                  >
                    <DatePicker style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
          </Col>

          {/* Company Information */}
          <Col xs={24} lg={12}>
            <Card title="Company Information" style={{ marginBottom: 24 }}>
              <Form.Item label="Select Company">
                <Select
                  value={selectedCompany?.id}
                  onChange={handleCompanyChange}
                  placeholder="Select a company"
                >
                  {companies.map(company => (
                    <Option key={company.id} value={company.id}>
                      {company.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
              <Row gutter={16}>
                <Col span={24}>
                  <Form.Item name="company_name" label="Name" rules={[{ required: true }]}>
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={24}>
                  <Form.Item name="company_address" label="Address">
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="company_city" label="City">
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="company_state" label="State">
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="company_zip" label="ZIP">
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="company_phone" label="Phone">
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="company_email" label="Email">
                    <Input type="email" />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
          </Col>

          {/* Client Information */}
          <Col xs={24} lg={12}>
            <Card title="Client Information" style={{ marginBottom: 24 }}>
              <Row gutter={16}>
                <Col span={24}>
                  <Form.Item
                    name="client_name"
                    label="Client Name"
                    rules={[{ required: true, message: 'Please enter client name' }]}
                  >
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={24}>
                  <Form.Item name="client_address" label="Address">
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="client_city" label="City">
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="client_state" label="State">
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="client_zip" label="ZIP">
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="client_phone" label="Phone">
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="client_email" label="Email">
                    <Input type="email" />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
          </Col>

          {/* Insurance Information */}
          <Col xs={24} lg={12}>
            <Card 
              title={
                <Space>
                  <span>Insurance Information</span>
                  <Switch
                    checked={showInsurance}
                    onChange={setShowInsurance}
                    checkedChildren="Yes"
                    unCheckedChildren="No"
                  />
                </Space>
              }
              style={{ marginBottom: 24 }}
            >
              {showInsurance && (
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item name="insurance_company" label="Insurance Company">
                      <Input />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="insurance_policy_number" label="Policy Number">
                      <Input />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="insurance_claim_number" label="Claim Number">
                      <Input />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="insurance_deductible" label="Deductible">
                      <InputNumber
                        style={{ width: '100%' }}
                        formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                        parser={value => value!.replace(/\$\s?|(,*)/g, '')}
                      />
                    </Form.Item>
                  </Col>
                </Row>
              )}
            </Card>
          </Col>
        </Row>

        {/* Invoice Items */}
        <Card
          title="Invoice Items"
          style={{ marginBottom: 24 }}
          extra={
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleAddItem}
            >
              Add Item
            </Button>
          }
        >
          <Table
            dataSource={items}
            columns={columns}
            pagination={false}
            rowKey={(_, index) => index?.toString() || '0'}
            summary={() => (
              <Table.Summary>
                <Table.Summary.Row>
                  <Table.Summary.Cell index={0} colSpan={6} align="right">
                    <strong>Subtotal:</strong>
                  </Table.Summary.Cell>
                  <Table.Summary.Cell index={1} align="right">
                    <strong>${totals.subtotal.toFixed(2)}</strong>
                  </Table.Summary.Cell>
                  <Table.Summary.Cell index={2} />
                </Table.Summary.Row>
              </Table.Summary>
            )}
          />
        </Card>

        {/* Totals and Additional Info */}
        <Row gutter={24}>
          <Col xs={24} lg={12}>
            <Card title="Additional Information" style={{ marginBottom: 24 }}>
              <Form.Item name="payment_terms" label="Payment Terms">
                <TextArea rows={2} placeholder="Net 30 days" />
              </Form.Item>
              <Form.Item name="notes" label="Notes">
                <TextArea rows={4} placeholder="Additional notes or instructions" />
              </Form.Item>
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card title="Payment Summary" style={{ marginBottom: 24 }}>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="discount" label="Discount">
                    <InputNumber
                      style={{ width: '100%' }}
                      min={0}
                      formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={value => value!.replace(/\$\s?|(,*)/g, '') as any}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="tax_rate" label="Tax Rate (%)">
                    <InputNumber
                      style={{ width: '100%' }}
                      min={0}
                      max={100}
                      formatter={value => `${value}%`}
                      parser={value => value!.replace('%', '') as any}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="shipping" label="Shipping">
                    <InputNumber
                      style={{ width: '100%' }}
                      min={0}
                      formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={value => value!.replace(/\$\s?|(,*)/g, '') as any}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="paid_amount" label="Paid Amount">
                    <InputNumber
                      style={{ width: '100%' }}
                      min={0}
                      formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={value => value!.replace(/\$\s?|(,*)/g, '') as any}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Divider />

              <div style={{ fontSize: '16px' }}>
                <Row justify="space-between" style={{ marginBottom: 8 }}>
                  <Col>Subtotal:</Col>
                  <Col>${totals.subtotal.toFixed(2)}</Col>
                </Row>
                {form.getFieldValue('discount') > 0 && (
                  <Row justify="space-between" style={{ marginBottom: 8 }}>
                    <Col>Discount:</Col>
                    <Col>-${(form.getFieldValue('discount') || 0).toFixed(2)}</Col>
                  </Row>
                )}
                {totals.taxAmount > 0 && (
                  <Row justify="space-between" style={{ marginBottom: 8 }}>
                    <Col>Tax ({form.getFieldValue('tax_rate') || 0}%):</Col>
                    <Col>${totals.taxAmount.toFixed(2)}</Col>
                  </Row>
                )}
                {form.getFieldValue('shipping') > 0 && (
                  <Row justify="space-between" style={{ marginBottom: 8 }}>
                    <Col>Shipping:</Col>
                    <Col>${(form.getFieldValue('shipping') || 0).toFixed(2)}</Col>
                  </Row>
                )}
                <Divider />
                <Row justify="space-between" style={{ fontWeight: 'bold', fontSize: '18px' }}>
                  <Col>Total:</Col>
                  <Col>${totals.total.toFixed(2)}</Col>
                </Row>
                {form.getFieldValue('paid_amount') > 0 && (
                  <>
                    <Row justify="space-between" style={{ marginTop: 8 }}>
                      <Col>Paid:</Col>
                      <Col>${(form.getFieldValue('paid_amount') || 0).toFixed(2)}</Col>
                    </Row>
                    <Row justify="space-between" style={{ fontWeight: 'bold', color: '#ff4d4f' }}>
                      <Col>Balance Due:</Col>
                      <Col>${(totals.total - (form.getFieldValue('paid_amount') || 0)).toFixed(2)}</Col>
                    </Row>
                  </>
                )}
              </div>
            </Card>
          </Col>
        </Row>

        {/* Action Buttons */}
        <Card>
          <Space size="middle">
            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={() => handleSave('draft')}
              loading={loading}
            >
              Save as Draft
            </Button>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={() => handleSave('sent')}
              loading={loading}
            >
              Save & Send
            </Button>
            <Button
              icon={<EyeOutlined />}
              onClick={handlePreviewPDF}
              loading={loading}
            >
              Preview PDF
            </Button>
            <Button
              onClick={() => navigate('/invoices')}
            >
              Cancel
            </Button>
          </Space>
        </Card>
      </Form>

      {/* Item Modal */}
      <Modal
        title={editingItem ? 'Edit Item' : 'Add Item'}
        open={itemModalVisible}
        onOk={handleItemSubmit}
        onCancel={() => {
          setItemModalVisible(false);
          itemForm.resetFields();
        }}
        width={600}
      >
        <Form
          form={itemForm}
          layout="vertical"
          initialValues={{
            quantity: 1,
            unit: 'ea',
            rate: 0,
          }}
        >
          <Form.Item
            name="name"
            label="Item Name"
            rules={[{ required: true, message: 'Please enter item name' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="description"
            label="Description"
          >
            <TextArea rows={3} />
          </Form.Item>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="quantity"
                label="Quantity"
                rules={[{ required: true }]}
              >
                <InputNumber style={{ width: '100%' }} min={0} step={1} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="unit"
                label="Unit"
                rules={[{ required: true }]}
              >
                <Select>
                  <Option value="ea">Each</Option>
                  <Option value="hr">Hour</Option>
                  <Option value="day">Day</Option>
                  <Option value="sqft">Sq Ft</Option>
                  <Option value="lf">Linear Ft</Option>
                  <Option value="gal">Gallon</Option>
                  <Option value="box">Box</Option>
                  <Option value="roll">Roll</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="rate"
                label="Rate"
                rules={[{ required: true }]}
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  step={0.01}
                  formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                  parser={((value: any) => parseFloat(value!.replace(/\$\s?|(,*)/g, '')) || 0) as any}
                />
              </Form.Item>
            </Col>
          </Row>
          {itemForm.getFieldValue('quantity') && itemForm.getFieldValue('rate') ? (
            <div style={{ textAlign: 'right', fontSize: '16px', fontWeight: 'bold' }}>
              Total: ${(itemForm.getFieldValue('quantity') * itemForm.getFieldValue('rate')).toFixed(2)}
            </div>
          ) : null}
        </Form>
      </Modal>
    </div>
  );
};

export default InvoiceCreation;