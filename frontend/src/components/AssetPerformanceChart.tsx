import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell } from 'recharts';

type AssetPerformanceChartProps = {
  data: { asset: string; gains: number; operations: number }[];
};

const AssetPerformanceChart: React.FC<AssetPerformanceChartProps> = ({ data }) => {
  if (!data.length) {
    return null;
  }

  const sorted = [...data].sort((a, b) => Math.abs(b.gains) - Math.abs(a.gains)).slice(0, 10);

  return (
    <div className="panel chart-panel">
      <div className="panel-header">
        <div>
          <p className="panel-label">Rentabilidad por activo</p>
          <h2>Top ganadores y perdedores</h2>
        </div>
      </div>
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={sorted} layout="vertical" margin={{ left: 40, right: 20, top: 12, bottom: 12 }}>
            <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} />
            <XAxis type="number" tickFormatter={(value) => `${value >= 0 ? '' : '-'}€${Math.abs(value).toFixed(0)}`} />
            <YAxis type="category" dataKey="asset" width={80} />
            <Tooltip
              formatter={(value: number, _name, props) => [
                `${value >= 0 ? '+' : ''}${value.toFixed(2)}€`,
                `${props?.payload?.operations ?? 0} operaciones`
              ]}
            />
            <Bar dataKey="gains" radius={[0, 8, 8, 0]}>
              {sorted.map((entry) => (
                <Cell key={entry.asset} fill={entry.gains >= 0 ? '#22c55e' : '#ef4444'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default AssetPerformanceChart;
