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
const formatDate = (value: string) =>
  new Intl.DateTimeFormat('es-ES', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(value));

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
    <div className="panel panel-table">
      <div className="panel-header panel-header--stacked">
        <div>
          <p className="panel-label">Historial detallado</p>
          <h2>Operaciones</h2>
        </div>
        <div className="filters-grid">
          <input
            type="date"
            value={filters.startDate || ''}
            onChange={(e) => onFiltersChange({ ...filters, startDate: e.target.value })}
            aria-label="Fecha inicio"
            className="control"
          />
          <input
            type="date"
            value={filters.endDate || ''}
            onChange={(e) => onFiltersChange({ ...filters, endDate: e.target.value })}
            aria-label="Fecha fin"
            className="control"
          />
          <select
            value={filters.asset || ''}
            onChange={(e) => onFiltersChange({ ...filters, asset: e.target.value || undefined })}
            className="control control--select"
          >
            <option value="">Todos los activos</option>
            {assets.map((asset) => (
              <option key={asset} value={asset}>
                {asset}
              </option>
            ))}
          </select>
          <select
            value={filters.type || ''}
            onChange={(e) => onFiltersChange({ ...filters, type: e.target.value || undefined })}
            className="control control--select"
          >
            <option value="">Todos los tipos</option>
            {types.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Activo</th>
              <th>Tipo</th>
              <th>Cantidad</th>
              <th>Precio EUR</th>
              <th>Comisión EUR</th>
              <th>Total EUR</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((operation) => (
              <tr key={operation.id}>
                <td>{formatDate(operation.date)}</td>
                <td>
                  <span className="chip">{operation.asset}</span>
                </td>
                <td>
                  <span className={`chip chip--${operation.type.toLowerCase()}`}>{operation.type}</span>
                </td>
                <td>{operation.amount}</td>
                <td>{formatCurrency(operation.price)}</td>
                <td>{operation.fee ? formatCurrency(operation.fee) : '-'}</td>
                <td>{operation.total ? formatCurrency(operation.total) : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!filtered.length && <p className="empty-state">No hay operaciones para los filtros seleccionados.</p>}
      </div>
    </div>
  );
};

export default OperationsTable;
