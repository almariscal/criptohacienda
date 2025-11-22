import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { GainPoint } from '../api/client';

interface GainsChartProps {
  data: GainPoint[];
  groupBy: 'day' | 'month' | 'year';
  onGroupByChange: (value: 'day' | 'month' | 'year') => void;
}

const GainsChart: React.FC<GainsChartProps> = ({ data, groupBy, onGroupByChange }) => {
  return (
    <div className="section">
      <div className="layout-header" style={{ padding: 0, marginBottom: 12 }}>
        <h2>Ganancias por periodo</h2>
        <select value={groupBy} onChange={(e) => onGroupByChange(e.target.value as 'day' | 'month' | 'year')}>
          <option value="day">Día</option>
          <option value="month">Mes</option>
          <option value="year">Año</option>
        </select>
      </div>
      <div style={{ width: '100%', height: 320 }}>
        <ResponsiveContainer>
          <BarChart data={data} margin={{ top: 12, bottom: 12, left: 0, right: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="period" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="gain" fill="#2563eb" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default GainsChart;
