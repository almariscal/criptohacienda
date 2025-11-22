import { PortfolioSnapshot } from '../api/client';
import { ResponsiveContainer, AreaChart, Area, XAxis, Tooltip, Legend } from 'recharts';

type PortfolioCompositionChartProps = {
  data: PortfolioSnapshot[];
};

const palette = ['#8b5cf6', '#0ea5e9', '#14b8a6', '#f97316', '#ec4899', '#facc15'];

const PortfolioCompositionChart: React.FC<PortfolioCompositionChartProps> = ({ data }) => {
  if (!data.length) {
    return null;
  }

  const lastSnapshot = data[data.length - 1];
  const sortedAssets = Object.entries(lastSnapshot.assetValues)
    .sort((a, b) => b[1] - a[1])
    .map(([asset]) => asset);
  const topAssets = sortedAssets.slice(0, 5);

  const chartData = data.map((point) => {
    const row: Record<string, number | string> = { timestamp: new Date(point.timestamp).toLocaleDateString('es-ES') };
    const others = Object.entries(point.assetValues).reduce(
      (acc, [asset, value]) => (topAssets.includes(asset) ? acc : acc + value),
      0
    );
    topAssets.forEach((asset) => {
      row[asset] = point.assetValues[asset] || 0;
    });
    if (others > 0) {
      row.Otros = others;
    }
    return row;
  });

  const series = [...topAssets, ...(chartData.some((row) => 'Otros' in row) ? ['Otros'] : [])];

  return (
    <div className="panel chart-panel">
      <div className="panel-header panel-header--stacked">
        <div>
          <p className="panel-label">Composición</p>
          <h2>Distribución por activo</h2>
        </div>
      </div>
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} stackOffset="expand" margin={{ top: 12, right: 20, left: 0, bottom: 12 }}>
            <XAxis dataKey="timestamp" />
            <Tooltip formatter={(value: number) => `${(value * 100).toFixed(2)}%`} />
            <Legend />
            {series.map((asset, index) => (
              <Area
                key={asset}
                type="monotone"
                dataKey={asset}
                stackId="1"
                stroke={palette[index % palette.length]}
                fill={palette[index % palette.length]}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default PortfolioCompositionChart;
