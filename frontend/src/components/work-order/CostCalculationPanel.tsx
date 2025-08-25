import React, { useState, useEffect } from 'react';
import {
  Card,
  Typography,
  Row,
  Col,
  InputNumber,
  Switch,
  Divider,
  Space,
  Tag,
  Tooltip,
  Alert,
  Spin
} from 'antd';
import {
  DollarOutlined,
  CreditCardOutlined,
  CalculatorOutlined,
  InfoCircleOutlined,
  EditOutlined
} from '@ant-design/icons';
import { CostBreakdown, Credit } from '../../types';

const { Title, Text } = Typography;

interface CostCalculationPanelProps {
  documentType: string;
  selectedTrades: string[];
  availableCredits: Credit[];
  companyId: string;
  onCostChange: (cost: number) => void;
  loading?: boolean;
}

const CostCalculationPanel: React.FC<CostCalculationPanelProps> = ({
  documentType,
  selectedTrades,
  availableCredits,
  companyId,
  onCostChange,
  loading = false
}) => {
  const [costBreakdown, setCostBreakdown] = useState<CostBreakdown>({
    baseCost: 0,
    creditsApplied: 0,
    finalCost: 0,
    availableCredits: 0
  });
  const [manualOverride, setManualOverride] = useState(false);
  const [overrideCost, setOverrideCost] = useState<number>(0);
  const [selectedCredits, setSelectedCredits] = useState<string[]>([]);
  const [calculating, setCalculating] = useState(false);

  // Mock base costs for document types
  const documentTypeCosts = {
    estimate: 50,
    invoice: 0,
    insurance_estimate: 100,
    plumber_report: 200
  };

  // Mock trade costs
  const tradeCosts = {
    plumbing: 150,
    electrical: 200,
    hvac: 300,
    carpentry: 120,
    painting: 80,
    roofing: 400,
    flooring: 250,
    drywall: 100
  };

  // Calculate costs when inputs change
  useEffect(() => {
    if (!documentType) return;

    setCalculating(true);

    // Simulate API delay
    const timer = setTimeout(() => {
      const baseDocumentCost = documentTypeCosts[documentType as keyof typeof documentTypeCosts] || 0;
      const tradesCost = selectedTrades.reduce((total, trade) => {
        return total + (tradeCosts[trade.toLowerCase() as keyof typeof tradeCosts] || 0);
      }, 0);
      
      const totalBaseCost = baseDocumentCost + tradesCost;
      
      // Calculate credits
      const totalAvailableCredits = availableCredits.reduce((sum, credit) => 
        credit.is_active ? sum + credit.amount : sum, 0
      );
      
      // Calculate applied credits (for now, just use available credits up to base cost)
      const appliedCredits = Math.min(totalAvailableCredits, totalBaseCost * 0.8); // Max 80% of base cost
      
      const finalCalculatedCost = Math.max(0, totalBaseCost - appliedCredits);

      const newBreakdown: CostBreakdown = {
        baseCost: totalBaseCost,
        creditsApplied: appliedCredits,
        finalCost: manualOverride ? overrideCost : finalCalculatedCost,
        availableCredits: totalAvailableCredits
      };

      setCostBreakdown(newBreakdown);
      onCostChange(newBreakdown.finalCost);
      setCalculating(false);
    }, 500);

    return () => clearTimeout(timer);
  }, [documentType, selectedTrades, availableCredits, manualOverride, overrideCost, companyId, onCostChange]);

  const handleManualOverride = (enabled: boolean) => {
    setManualOverride(enabled);
    if (enabled) {
      setOverrideCost(costBreakdown.finalCost);
    }
  };

  const handleOverrideCostChange = (value: number | null) => {
    const newCost = value || 0;
    setOverrideCost(newCost);
    if (manualOverride) {
      onCostChange(newCost);
    }
  };

  return (
    <Card 
      title={
        <Space>
          <CalculatorOutlined />
          <span>Cost Calculation</span>
        </Space>
      }
      extra={
        <Tooltip title="Enable to manually override the calculated cost">
          <Space>
            <EditOutlined />
            <Switch
              size="small"
              checked={manualOverride}
              onChange={handleManualOverride}
              checkedChildren="Manual"
              unCheckedChildren="Auto"
            />
          </Space>
        </Tooltip>
      }
    >
      <Spin spinning={calculating || loading}>
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          
          {/* Base Cost Breakdown */}
          <div>
            <Title level={5} style={{ margin: 0, marginBottom: 8 }}>
              <DollarOutlined style={{ marginRight: 8, color: '#1890ff' }} />
              Cost Breakdown
            </Title>
            
            <Row gutter={[16, 8]}>
              <Col span={24}>
                <div style={{ background: '#f5f5f5', padding: '12px', borderRadius: '6px' }}>
                  <Row justify="space-between" style={{ marginBottom: 4 }}>
                    <Col>
                      <Text style={{ fontSize: '12px' }}>Document Type ({documentType}):</Text>
                    </Col>
                    <Col>
                      <Text style={{ fontSize: '12px' }}>
                        ${documentTypeCosts[documentType as keyof typeof documentTypeCosts] || 0}
                      </Text>
                    </Col>
                  </Row>
                  
                  {selectedTrades.map(trade => (
                    <Row key={trade} justify="space-between" style={{ marginBottom: 4 }}>
                      <Col>
                        <Text style={{ fontSize: '12px' }}>{trade}:</Text>
                      </Col>
                      <Col>
                        <Text style={{ fontSize: '12px' }}>
                          ${tradeCosts[trade.toLowerCase() as keyof typeof tradeCosts] || 0}
                        </Text>
                      </Col>
                    </Row>
                  ))}
                  
                  <Divider style={{ margin: '8px 0' }} />
                  <Row justify="space-between">
                    <Col>
                      <Text strong>Base Cost:</Text>
                    </Col>
                    <Col>
                      <Text strong>${costBreakdown.baseCost.toFixed(2)}</Text>
                    </Col>
                  </Row>
                </div>
              </Col>
            </Row>
          </div>

          {/* Credits Section */}
          <div>
            <Title level={5} style={{ margin: 0, marginBottom: 8 }}>
              <CreditCardOutlined style={{ marginRight: 8, color: '#52c41a' }} />
              Available Credits
            </Title>
            
            {availableCredits.length > 0 ? (
              <div>
                <Space wrap style={{ marginBottom: 8 }}>
                  {availableCredits.map(credit => (
                    <Tag 
                      key={credit.id}
                      color={credit.is_active ? 'green' : 'red'}
                      style={{ fontSize: '11px' }}
                    >
                      ${credit.amount} - {credit.description}
                    </Tag>
                  ))}
                </Space>
                <Row justify="space-between" style={{ marginBottom: 8 }}>
                  <Col>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      Total Available:
                    </Text>
                  </Col>
                  <Col>
                    <Text style={{ fontSize: '12px', color: '#52c41a' }}>
                      ${costBreakdown.availableCredits.toFixed(2)}
                    </Text>
                  </Col>
                </Row>
                <Row justify="space-between">
                  <Col>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      Credits Applied:
                    </Text>
                  </Col>
                  <Col>
                    <Text style={{ fontSize: '12px', color: '#52c41a' }}>
                      -${costBreakdown.creditsApplied.toFixed(2)}
                    </Text>
                  </Col>
                </Row>
              </div>
            ) : (
              <Alert
                message="No credits available"
                type="info"
                showIcon
                icon={<InfoCircleOutlined />}
              />
            )}
          </div>

          {/* Manual Override Section */}
          {manualOverride && (
            <div>
              <Title level={5} style={{ margin: 0, marginBottom: 8 }}>
                Manual Cost Override
              </Title>
              <InputNumber
                style={{ width: '100%' }}
                value={overrideCost}
                onChange={handleOverrideCostChange}
                min={0}
                precision={2}
                formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                parser={value => value!.replace(/\$\s?|(,*)/g, '') as any}
                size="large"
              />
              <Text type="warning" style={{ fontSize: '11px', display: 'block', marginTop: 4 }}>
                Manual override is enabled. Auto-calculation is disabled.
              </Text>
            </div>
          )}

          {/* Final Cost */}
          <div>
            <Divider />
            <Row 
              justify="space-between" 
              align="middle"
              style={{ 
                padding: '12px',
                background: '#f0f9ff',
                borderRadius: '6px',
                border: '1px solid #d1ecf1'
              }}
            >
              <Col>
                <Title level={4} style={{ margin: 0, color: '#1890ff' }}>
                  Final Cost:
                </Title>
              </Col>
              <Col>
                <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
                  ${costBreakdown.finalCost.toFixed(2)}
                </Title>
              </Col>
            </Row>
          </div>

          {/* Cost Summary */}
          <div style={{ fontSize: '11px', color: '#666' }}>
            <Text type="secondary">
              Base: ${costBreakdown.baseCost.toFixed(2)} • 
              Credits: -${costBreakdown.creditsApplied.toFixed(2)} • 
              Final: ${costBreakdown.finalCost.toFixed(2)}
              {manualOverride && ' (Manual Override)'}
            </Text>
          </div>
        </Space>
      </Spin>
    </Card>
  );
};

export default CostCalculationPanel;