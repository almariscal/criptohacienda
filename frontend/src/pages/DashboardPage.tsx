import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import GainsChart from '../components/GainsChart';
import OperationsTable from '../components/OperationsTable';
import SummaryCards from '../components/SummaryCards';
import { DashboardResponse, apiClient } from '../api/client';
import { useSession } from '../context/SessionContext';

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
      <div className="section">
        <h2>Posiciones actuales</h2>
        <table>
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
                <td>
                  {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' }).format(holding.averagePrice)}
                </td>
                <td>
                  {new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' }).format(holding.currentValue)}
                </td>
              </tr>
            ))}
            {!data.holdings.length && (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: '16px' }}>
                  No hay posiciones cargadas todavía.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    );
  }, [data]);

  if (!sessionId) {
    return (
      <div className="section">
        <h2>Dashboard</h2>
        <p>Sube primero un CSV para generar una sesión de análisis.</p>
        <Link to="/">Ir a subir CSV</Link>
      </div>
    );
  }

  return (
    <div>
      {loading && <div className="alert">Cargando datos...</div>}
      {error && <div className="alert">{error}</div>}
      {data && <SummaryCards summary={data.summary} />}
      {data && <GainsChart data={data.gains} groupBy={groupBy} onGroupByChange={setGroupBy} />}
      {data && (
        <div className="section">
          <div className="layout-header" style={{ padding: 0 }}>
            <h2>Filtros y exportación</h2>
            <button onClick={handleExport} disabled={loading}>
              Exportar CSV
            </button>
          </div>
          <p style={{ marginTop: 8 }}>Ajusta los filtros en la tabla para exportar exactamente las operaciones que necesitas.</p>
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
