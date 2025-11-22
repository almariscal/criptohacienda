import { SummaryResponse } from '../api/client';
import { ResponsiveContainer, BarChart, Bar, XAxis, Tooltip, Cell } from 'recharts';

const currency = new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' });

type FundsFlowChartProps = {
  summary: SummaryResponse;
};

const palette = ['#6366f1', '#14b8a6', '#f97316'];

const FundsFlowChart: React.FC<FundsFlowChartProps> = ({ summary }) => {
  const data = [
    { label: 'Entrado', value: summary.totalInvested },
    { label: 'Dentro', value: summary.currentBalance },
    { label: 'Salido', value: summary.totalWithdrawn }
  ];

  return (
    <div className="panel chart-panel">
      <div className="panel-header panel-header--stacked">
        <div>
          <p className="panel-label">Flujo de fondos</p>
          <h2>Entradas, saldo y salidas</h2>
        </div>
      </div>
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 12, right: 12, left: 0, bottom: 12 }}>
            <XAxis dataKey="label" axisLine={false} tickLine={false} />
            <Tooltip
              formatter={(value: number) => currency.format(value)}
              labelFormatter={(label) => label}
              cursor={{ fill: 'rgba(99, 102, 241, 0.06)' }}
            />
            <Bar dataKey="value" radius={[12, 12, 12, 12]}>
              {data.map((entry, index) => (
                <Cell key={entry.label} fill={palette[index % palette.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default FundsFlowChart;
