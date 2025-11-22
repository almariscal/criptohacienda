import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { GainPoint } from '../api/client';

interface GainsChartProps {
  data: GainPoint[];
  groupBy: 'day' | 'month' | 'year';
  onGroupByChange: (value: 'day' | 'month' | 'year') => void;
}

const GainsChart: React.FC<GainsChartProps> = ({ data, groupBy, onGroupByChange }) => {
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
      <div className="chart-wrapper">
        <ResponsiveContainer>
          <BarChart data={data} margin={{ top: 12, bottom: 12, left: 0, right: 0 }}>
            <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} />
            <XAxis dataKey="period" stroke="var(--text-muted)" />
            <YAxis stroke="var(--text-muted)" />
            <Tooltip
              contentStyle={{
                background: 'var(--surface)',
                border: `1px solid var(--border-color)`,
                borderRadius: '12px'
              }}
            />
            <Bar dataKey="gain" fill="var(--accent-color)" radius={[12, 12, 12, 12]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default GainsChart;
