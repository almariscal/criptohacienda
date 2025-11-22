import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import GainsChart from '../components/GainsChart';
import OperationsTable from '../components/OperationsTable';
import SummaryCards from '../components/SummaryCards';
import FundsFlowChart from '../components/FundsFlowChart';
import PortfolioHistoryChart from '../components/PortfolioHistoryChart';
import PortfolioCompositionChart from '../components/PortfolioCompositionChart';
import { DashboardResponse, apiClient } from '../api/client';
import { useSession } from '../context/SessionContext';

const currency = new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' });

const DashboardPage = () => {
  const { sessionId } = useSession();
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [groupBy, setGroupBy] = useState<'day' | 'month' | 'year'>('month');
  const [filters, setFilters] = useState({ startDate: '', endDate: '', asset: '', type: '' });

  useEffect(() => {
    const fetchData = async () => {
      if (!sessionId) return;
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.fetchDashboard(sessionId, {
          groupBy,
          startDate: filters.startDate || undefined,
          endDate: filters.endDate || undefined,
          asset: filters.asset || undefined,
          type: filters.type || undefined
        });
        setData(response);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [sessionId, groupBy, filters.startDate, filters.endDate, filters.asset, filters.type]);

  const handleExport = async () => {
    if (!sessionId) return;
    const blob = await apiClient.exportOperationsCsv(sessionId, {
      startDate: filters.startDate || undefined,
      endDate: filters.endDate || undefined,
      asset: filters.asset || undefined,
      type: filters.type || undefined
    });

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'operations.csv');
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  const holdingsView = useMemo(() => {
    if (!data) return null;
    return (
      <div className="panel panel-holdings">
        <div className="panel-header">
          <div>
            <p className="panel-label">Estado actual</p>
            <h2>Posiciones abiertas</h2>
          </div>
        </div>
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Activo</th>
                <th>Cantidad</th>
                <th>Precio promedio</th>
                <th>Valor actual</th>
              </tr>
            </thead>
            <tbody>
              {data.holdings.map((holding) => (
                <tr key={holding.asset}>
                  <td>{holding.asset}</td>
                  <td>{holding.quantity}</td>
                  <td>{currency.format(holding.averagePrice)}</td>
                  <td>{currency.format(holding.currentValue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!data.holdings.length && <p className="empty-state">No hay posiciones cargadas todavía.</p>}
        </div>
      </div>
    );
  }, [data]);

  if (!sessionId) {
    return (
      <div className="panel panel-empty">
        <h2>Dashboard</h2>
        <p>Sube primero un CSV para generar una sesión de análisis.</p>
        <Link to="/" className="btn btn-primary">
          Ir a subir CSV
        </Link>
      </div>
    );
  }

  return (
    <div className="dashboard-stack">
      {loading && <div className="status-badge">Cargando datos...</div>}
      {error && <div className="status-badge status-badge--error">{error}</div>}
      {data && <SummaryCards summary={data.summary} />}
      {data && <FundsFlowChart summary={data.summary} />}
      {data && <PortfolioHistoryChart data={data.portfolioHistory} />}
      {data && <PortfolioCompositionChart data={data.portfolioHistory} />}
      {data && <GainsChart data={data.gains} groupBy={groupBy} onGroupByChange={setGroupBy} />}
      {data && (
        <div className="panel panel-info">
          <div className="panel-header">
            <div>
              <p className="panel-label">Exportación</p>
              <h2>Filtros rápidos</h2>
            </div>
            <button onClick={handleExport} className="btn ghost" disabled={loading}>
              Exportar CSV
            </button>
          </div>
          <p>Ajusta los filtros en la tabla y descárgalos exactamente como los ves en pantalla.</p>
        </div>
      )}
      {data && (
        <OperationsTable
          operations={data.operations}
          filters={filters}
          onFiltersChange={(newFilters) => setFilters({ ...filters, ...newFilters })}
        />
      )}
      {data && holdingsView}
    </div>
  );
};

export default DashboardPage;
