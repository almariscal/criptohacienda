import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, Cell } from 'recharts';
import { GainPoint } from '../api/client';

interface GainsChartProps {
  data: GainPoint[];
  groupBy: 'day' | 'month' | 'year';
  onGroupByChange: (value: 'day' | 'month' | 'year') => void;
}

const GainsTooltip = ({ active, payload }: { active?: boolean; payload?: any[] }) => {
  if (!active || !payload || !payload.length) {
    return null;
  }
  const point: GainPoint = payload[0].payload;
  const details = point.details || [];
  return (
    <div className="chart-tooltip">
      <strong>{point.period}</strong>
      <p className={point.gain >= 0 ? 'positive' : 'negative'}>
        {point.gain >= 0 ? '+' : ''}
        {point.gain.toFixed(2)}€
      </p>
      <ul>
        {details.slice(0, 5).map((detail, index) => (
          <li key={`${detail.asset}-${detail.timestamp}-${index}`}>
            <span>{new Date(detail.timestamp).toLocaleDateString('es-ES')}</span> · {detail.asset}{' '}
            {detail.gain >= 0 ? '+' : ''}
            {detail.gain.toFixed(2)}€
          </li>
        ))}
        {details.length > 5 && <li>+{details.length - 5} operaciones más</li>}
        {details.length === 0 && <li>Sin movimientos en este periodo</li>}
      </ul>
    </div>
  );
};

const GainsChart: React.FC<GainsChartProps> = ({ data, groupBy, onGroupByChange }) => {
  const length = Math.max(data.length, 1);
  const chartWidth = Math.max(600, length * 80);

  return (
    <div className="panel chart-panel">
      <div className="panel-header">
        <div>
          <p className="panel-label">Balance temporal</p>
          <h2>Ganancias por periodo</h2>
        </div>
        <select
          value={groupBy}
          onChange={(e) => onGroupByChange(e.target.value as 'day' | 'month' | 'year')}
          className="control control--select"
        >
          <option value="day">Día</option>
          <option value="month">Mes</option>
          <option value="year">Año</option>
        </select>
      </div>
      <div className="chart-wrapper chart-scroll">
        <div style={{ width: chartWidth, height: '320px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 12, bottom: 12, left: 0, right: 0 }}>
              <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} />
              <XAxis dataKey="period" stroke="var(--text-muted)" />
              <YAxis
                stroke="var(--text-muted)"
                tickFormatter={(value) => `${value >= 0 ? '' : '-'}€${Math.abs(value).toFixed(0)}`}
              />
              <Tooltip content={<GainsTooltip />} />
              <Bar dataKey="gain" radius={[12, 12, 12, 12]}>
                {data.map((entry) => (
                  <Cell key={entry.period} fill={entry.gain >= 0 ? '#22c55e' : '#ef4444'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default GainsChart;
