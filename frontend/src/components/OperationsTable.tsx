import { useMemo } from 'react';
import { Operation } from '../api/client';

type FilterState = {
  startDate?: string;
  endDate?: string;
  asset?: string;
  type?: string;
};

interface OperationsTableProps {
  operations: Operation[];
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
}

const formatCurrency = (value: number) => new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' }).format(value);

const OperationsTable: React.FC<OperationsTableProps> = ({ operations, filters, onFiltersChange }) => {
  const assets = useMemo(() => Array.from(new Set(operations.map((op) => op.asset))).sort(), [operations]);
  const types = useMemo(() => Array.from(new Set(operations.map((op) => op.type))).sort(), [operations]);

  const filtered = operations.filter((op) => {
    if (filters.startDate && op.date < filters.startDate) return false;
    if (filters.endDate && op.date > filters.endDate) return false;
    if (filters.asset && op.asset !== filters.asset) return false;
    if (filters.type && op.type !== filters.type) return false;
    return true;
  });

  return (
    <div className="section">
      <div className="layout-header" style={{ padding: 0, marginBottom: 12 }}>
        <h2>Operaciones</h2>
        <div className="input-group" style={{ margin: 0 }}>
          <input
            type="date"
            value={filters.startDate || ''}
            onChange={(e) => onFiltersChange({ ...filters, startDate: e.target.value })}
            aria-label="Fecha inicio"
          />
          <input
            type="date"
            value={filters.endDate || ''}
            onChange={(e) => onFiltersChange({ ...filters, endDate: e.target.value })}
            aria-label="Fecha fin"
          />
          <select value={filters.asset || ''} onChange={(e) => onFiltersChange({ ...filters, asset: e.target.value || undefined })}>
            <option value="">Todos los activos</option>
            {assets.map((asset) => (
              <option key={asset} value={asset}>
                {asset}
              </option>
            ))}
          </select>
          <select value={filters.type || ''} onChange={(e) => onFiltersChange({ ...filters, type: e.target.value || undefined })}>
            <option value="">Todos los tipos</option>
            {types.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table>
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Activo</th>
              <th>Tipo</th>
              <th>Cantidad</th>
              <th>Precio</th>
              <th>Comisión</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((operation) => (
              <tr key={operation.id}>
                <td>{operation.date}</td>
                <td>{operation.asset}</td>
                <td>{operation.type}</td>
                <td>{operation.amount}</td>
                <td>{formatCurrency(operation.price)}</td>
                <td>{operation.fee ? formatCurrency(operation.fee) : '-'}</td>
                <td>{operation.total ? formatCurrency(operation.total) : '-'}</td>
              </tr>
            ))}
            {!filtered.length && (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '16px' }}>
                  No hay operaciones para los filtros seleccionados.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default OperationsTable;
