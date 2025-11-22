import { PortfolioSnapshot } from '../api/client';
import { ResponsiveContainer, LineChart, Line, XAxis, Tooltip, YAxis, CartesianGrid } from 'recharts';

type PortfolioHistoryChartProps = {
  data: PortfolioSnapshot[];
};

const formatCurrency = (value: number) => new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' }).format(value);

const PortfolioHistoryChart: React.FC<PortfolioHistoryChartProps> = ({ data }) => {
  if (!data.length) {
    return null;
  }

  const chartData = data.map((point) => ({
    timestamp: new Date(point.timestamp).toLocaleDateString('es-ES'),
    totalValue: point.totalValue
  }));

  return (
    <div className="panel chart-panel">
      <div className="panel-header panel-header--stacked">
        <div>
          <p className="panel-label">Valor de la cartera</p>
          <h2>Evolución total</h2>
        </div>
      </div>
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 12, right: 20, left: 0, bottom: 12 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
            <XAxis dataKey="timestamp" />
            <YAxis tickFormatter={(value) => `${Math.round(value / 1000)}k`} />
            <Tooltip formatter={(value: number) => formatCurrency(value)} />
            <Line type="monotone" dataKey="totalValue" stroke="#6366f1" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default PortfolioHistoryChart;
