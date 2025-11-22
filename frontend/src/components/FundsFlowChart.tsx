import { SummaryResponse } from '../api/client';
import { ResponsiveContainer, ComposedChart, Bar, XAxis, Tooltip, Cell, YAxis, ReferenceLine } from 'recharts';

const currency = new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' });

type FundsFlowChartProps = {
  summary: SummaryResponse;
};

const FlowTooltip = ({ active, payload }: { active?: boolean; payload?: any[] }) => {
  if (!active || !payload || !payload.length) return null;
  const item = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <strong>{item.label}</strong>
      <p className={item.amount >= 0 ? 'positive' : 'negative'}>
        {item.amount >= 0 ? '+' : '-'}
        {currency.format(Math.abs(item.amount))}
      </p>
      <p className="processing-description">{item.description}</p>
    </div>
  );
};

const FundsFlowChart: React.FC<FundsFlowChartProps> = ({ summary }) => {
  const net = summary.totalInvested - summary.totalWithdrawn;
  const data = [
    { label: 'Aportaciones', amount: summary.totalInvested, color: '#22c55e', description: 'Capital inyectado en el exchange' },
    { label: 'Saldo actual', amount: summary.currentBalance, color: '#6366f1', description: 'Valor vivo de tus activos' },
    { label: 'Retiros', amount: -summary.totalWithdrawn, color: '#ef4444', description: 'Fondos retirados a cuentas externas' }
  ];

  return (
    <div className="panel chart-panel">
      <div className="panel-header panel-header--stacked">
        <div>
          <p className="panel-label">Flujo de fondos</p>
          <h2>Entradas, saldo y salidas</h2>
        </div>
        <div className="status-badge">
          Balance neto:&nbsp;
          <strong className={net >= 0 ? 'positive' : 'negative'}>
            {net >= 0 ? '+' : '-'}
            {currency.format(Math.abs(net))}
          </strong>
        </div>
      </div>
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} layout="vertical" margin={{ top: 12, bottom: 12, left: 20, right: 20 }}>
            <XAxis type="number" tickFormatter={(value) => `${value >= 0 ? '' : '-'}€${Math.abs(value).toFixed(0)}`} />
            <YAxis type="category" dataKey="label" width={120} />
            <ReferenceLine x={0} stroke="var(--border-color)" />
            <Tooltip content={<FlowTooltip />} />
            <Bar dataKey="amount" barSize={26} radius={[0, 12, 12, 0]}>
              {data.map((entry) => (
                <Cell key={entry.label} fill={entry.color} />
              ))}
            </Bar>
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default FundsFlowChart;
